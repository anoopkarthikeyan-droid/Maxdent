import { useEffect, useMemo, useState } from "react"
import { listCustomers } from "../api/customers"
import { listDistributions } from "../api/distributions"
import { listQualityTypes } from "../api/qualityTypes"
import {
  createScheduler,
  deleteScheduler,
  getNextSchedulerCode,
  listSchedulers,
  updateScheduler,
} from "../api/schedulers"
import SchedulerCasePanel from "./SchedulerCasePanel"
import { listWorks } from "../api/works"

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function emptyDetail() {
  return {
    key: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    work_id: "",
    patient_name: "",
    arch: "Both",
    quality_type_id: "",
    additional_requirements: "",
    rate: "0",
    qty: "1",
    extra_charge: "0",
    discount: "0",
    remarks: "",
    scheduler_detail_id: null,
    has_case: false,
  }
}

const emptyForm = {
  customer_id: "",
  billing_party_id: "",
  sending_party_id: "",
  work_type: "New",
  work_received_date: todayIso(),
  completion_date: todayIso(),
}

function toNumber(value) {
  if (value === "" || value === null || value === undefined) return 0
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function finalRate(row) {
  return (
    toNumber(row.rate) * toNumber(row.qty) +
    toNumber(row.extra_charge) -
    toNumber(row.discount)
  )
}

function padWorkNo(mdoCode, index) {
  if (!mdoCode) return ""
  return `${mdoCode}#${String(index).padStart(2, "0")}`
}

function rateFromDistribution(distribution, workId, qualityName) {
  if (!distribution || !workId || !qualityName) return null
  const detail = (distribution.details || []).find(
    (item) => String(item.work_id) === String(workId),
  )
  if (!detail) return null
  const name = String(qualityName).toLowerCase()
  if (name.includes("plus")) return detail.supreme_plus_rate
  if (name.includes("supreme")) return detail.supreme_rate
  return detail.prime_rate
}

export default function SchedulerMaster() {
  const [items, setItems] = useState([])
  const [customers, setCustomers] = useState([])
  const [works, setWorks] = useState([])
  const [qualities, setQualities] = useState([])
  const [distributions, setDistributions] = useState([])
  const [search, setSearch] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [details, setDetails] = useState([emptyDetail()])
  const [previewCode, setPreviewCode] = useState("")
  const [editingId, setEditingId] = useState(null)
  const [savedCode, setSavedCode] = useState("")
  const [caseRow, setCaseRow] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  const mdoCode = editingId ? savedCode : previewCode

  const selectedCustomer = useMemo(
    () => customers.find((item) => String(item.customer_id) === String(form.customer_id)),
    [customers, form.customer_id],
  )

  const selectedDistribution = useMemo(
    () =>
      distributions.find(
        (item) =>
          String(item.distribution_id) === String(selectedCustomer?.distribution_id),
      ),
    [distributions, selectedCustomer],
  )

  const activeWorks = useMemo(
    () =>
      works.filter(
        (item) =>
          item.status === "Active" ||
          details.some((row) => String(row.work_id) === String(item.work_id)),
      ),
    [works, details],
  )

  const activeQualities = useMemo(
    () =>
      qualities.filter(
        (item) =>
          item.status === "Active" ||
          details.some(
            (row) => String(row.quality_type_id) === String(item.quality_type_id),
          ),
      ),
    [qualities, details],
  )

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listSchedulers(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadLookups() {
    try {
      const [customerData, workData, qualityData, distributionData] =
        await Promise.all([
          listCustomers(""),
          listWorks(""),
          listQualityTypes(""),
          listDistributions(""),
        ])
      setCustomers(customerData)
      setWorks(workData)
      setQualities(qualityData)
      setDistributions(distributionData)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load("")
    loadLookups()
  }, [])

  useEffect(() => {
    if (editingId || !form.customer_id || !form.work_received_date) {
      if (!editingId) setPreviewCode("")
      return
    }
    let cancelled = false
    getNextSchedulerCode(form.customer_id, form.work_received_date)
      .then((data) => {
        if (!cancelled) setPreviewCode(data.mdo_code)
      })
      .catch(() => {
        if (!cancelled) setPreviewCode("")
      })
    return () => {
      cancelled = true
    }
  }, [editingId, form.customer_id, form.work_received_date])

  function resetForm() {
    setForm({ ...emptyForm, work_received_date: todayIso(), completion_date: todayIso() })
    setDetails([emptyDetail()])
    setEditingId(null)
    setSavedCode("")
    setPreviewCode("")
    setCaseRow(null)
  }

  function applyCustomer(customerId) {
    const customer = customers.find(
      (item) => String(item.customer_id) === String(customerId),
    )
    setForm((prev) => ({
      ...prev,
      customer_id: customerId,
      billing_party_id: customer
        ? String(customer.billing_office_id || customer.customer_id)
        : "",
      sending_party_id: customer
        ? String(customer.head_office_id || customer.customer_id)
        : "",
    }))
  }

  function lookupRate(workId, qualityId) {
    const quality = qualities.find(
      (item) => String(item.quality_type_id) === String(qualityId),
    )
    const found = rateFromDistribution(
      selectedDistribution,
      workId,
      quality?.quality_name,
    )
    return found === null || found === undefined ? null : String(found)
  }

  function updateDetail(index, patch) {
    setDetails((prev) =>
      prev.map((row, rowIndex) => {
        if (rowIndex !== index) return row
        const next = { ...row, ...patch }
        if ("work_id" in patch || "quality_type_id" in patch) {
          const autoRate = lookupRate(next.work_id, next.quality_type_id)
          if (autoRate !== null) next.rate = autoRate
        }
        return next
      }),
    )
  }

  function onEdit(item) {
    setEditingId(item.scheduler_id)
    setSavedCode(item.mdo_code || "")
    setPreviewCode("")
    setForm({
      customer_id: String(item.customer_id || ""),
      billing_party_id: String(item.billing_party_id || ""),
      sending_party_id: String(item.sending_party_id || ""),
      work_type: item.work_type || "New",
      work_received_date: String(item.work_received_date || "").slice(0, 10),
      completion_date: String(item.completion_date || "").slice(0, 10),
    })
    setDetails(
      (item.details || []).map((row) => ({
        key: String(row.scheduler_detail_id),
        work_id: String(row.work_id || ""),
        patient_name: row.patient_name || "",
        arch: row.arch || "Both",
        quality_type_id: String(row.quality_type_id || ""),
        additional_requirements: row.additional_requirements || "",
        rate: String(row.rate ?? "0"),
        qty: String(row.qty ?? "1"),
        extra_charge: String(row.extra_charge ?? "0"),
        discount: String(row.discount ?? "0"),
        remarks: row.remarks || "",
        work_no: row.work_no || "",
        scheduler_detail_id: row.scheduler_detail_id || null,
        has_case: Boolean(row.has_case),
        case_approval_status: row.case_approval_status || null,
      })),
    )
    setMessage("")
    setError("")
  }

  async function onSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")

    const payload = {
      customer_id: Number(form.customer_id),
      billing_party_id: Number(form.billing_party_id),
      sending_party_id: Number(form.sending_party_id),
      work_type: form.work_type,
      work_received_date: form.work_received_date,
      completion_date: form.completion_date,
      details: details.map((row) => ({
        scheduler_detail_id: row.scheduler_detail_id || null,
        work_id: Number(row.work_id),
        patient_name: row.patient_name.trim(),
        arch: row.arch,
        quality_type_id: Number(row.quality_type_id),
        additional_requirements: row.additional_requirements.trim() || null,
        rate: toNumber(row.rate),
        qty: toNumber(row.qty),
        extra_charge: toNumber(row.extra_charge),
        discount: toNumber(row.discount),
        final_rate: finalRate(row),
        remarks: row.remarks.trim() || null,
      })),
    }

    try {
      let saved
      if (editingId) {
        saved = await updateScheduler(editingId, payload)
        setMessage("Scheduler updated successfully.")
      } else {
        saved = await createScheduler(payload)
        setMessage("Scheduler created successfully.")
      }
      onEdit(saved)
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(schedulerId, code) {
    const confirmed = window.confirm(
      `Delete scheduler "${code}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteScheduler(schedulerId)
      if (editingId === schedulerId) resetForm()
      setMessage("Scheduler deleted successfully.")
      await load(search)
    } catch (err) {
      setError(err.message)
    }
  }

  function onSearchSubmit(event) {
    event.preventDefault()
    load(search)
  }

  const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
  const compactClass =
    "w-full min-w-[7rem] rounded-md border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-slate-500"

  return (
    <div className="mx-auto max-w-[90rem] space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Scheduler Details</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete scheduler header and work details.
        </p>
      </header>

      {(error || message) && (
        <div
          className={`rounded-md px-4 py-3 text-sm ${
            error
              ? "border border-red-200 bg-red-50 text-red-700"
              : "border border-emerald-200 bg-emerald-50 text-emerald-700"
          }`}
        >
          {error || message}
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-6">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-lg font-medium text-slate-800">
            {editingId ? "Edit Header" : "Header"}
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Customer Name</span>
              <select
                required
                value={form.customer_id}
                onChange={(e) => applyCustomer(e.target.value)}
                className={inputClass}
              >
                <option value="">Select customer</option>
                {customers.map((item) => (
                  <option key={item.customer_id} value={item.customer_id}>
                    {item.branch_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">MdoCode</span>
              <input
                type="text"
                readOnly
                value={mdoCode}
                className={`${inputClass} bg-slate-100 text-slate-700`}
                placeholder="RouteCode-FinYear-OrderNo"
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Work Type</span>
              <select
                required
                value={form.work_type}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, work_type: e.target.value }))
                }
                className={inputClass}
              >
                <option value="New">New</option>
                <option value="Repeat">Repeat</option>
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Billing Party</span>
              <select
                required
                value={form.billing_party_id}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, billing_party_id: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">Select billing party</option>
                {customers.map((item) => (
                  <option key={`bill-${item.customer_id}`} value={item.customer_id}>
                    {item.branch_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Sending Party</span>
              <select
                required
                value={form.sending_party_id}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, sending_party_id: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">Select sending party</option>
                {customers.map((item) => (
                  <option key={`send-${item.customer_id}`} value={item.customer_id}>
                    {item.branch_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">
                Work Received Date
              </span>
              <input
                type="date"
                required
                value={form.work_received_date}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    work_received_date: e.target.value,
                  }))
                }
                className={inputClass}
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">
                Completion Date
              </span>
              <input
                type="date"
                required
                value={form.completion_date}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, completion_date: e.target.value }))
                }
                className={inputClass}
              />
            </label>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-medium text-slate-800">Detail</h2>
            <button
              type="button"
              onClick={() => setDetails((prev) => [...prev, emptyDetail()])}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Add Work
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    WorkNo
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Work Name
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Patient Name
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Arch
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Quality
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Additional Requirements
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Rate
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Qty
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Extra Charge
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Discount
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Final Rate
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Remarks
                  </th>
                  <th className="px-2 py-2 text-right font-semibold text-slate-700">
                    {" "}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {details.map((row, index) => (
                  <tr key={row.key}>
                    <td className="px-2 py-2 align-top whitespace-nowrap text-slate-700">
                      {row.work_no || padWorkNo(mdoCode, index + 1) || "-"}
                    </td>
                    <td className="px-2 py-2 align-top">
                      <select
                        required
                        value={row.work_id}
                        onChange={(e) =>
                          updateDetail(index, { work_id: e.target.value })
                        }
                        className={compactClass}
                      >
                        <option value="">Select work</option>
                        {activeWorks.map((item) => (
                          <option key={item.work_id} value={item.work_id}>
                            {item.work_name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="text"
                        required
                        maxLength={150}
                        value={row.patient_name}
                        onChange={(e) =>
                          updateDetail(index, { patient_name: e.target.value })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <select
                        required
                        value={row.arch}
                        onChange={(e) =>
                          updateDetail(index, { arch: e.target.value })
                        }
                        className={compactClass}
                      >
                        <option value="Upper">Upper</option>
                        <option value="Lower">Lower</option>
                        <option value="Both">Both</option>
                      </select>
                    </td>
                    <td className="px-2 py-2 align-top">
                      <select
                        required
                        value={row.quality_type_id}
                        onChange={(e) =>
                          updateDetail(index, { quality_type_id: e.target.value })
                        }
                        className={compactClass}
                      >
                        <option value="">Select quality</option>
                        {activeQualities.map((item) => (
                          <option
                            key={item.quality_type_id}
                            value={item.quality_type_id}
                          >
                            {item.quality_name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="text"
                        maxLength={500}
                        value={row.additional_requirements}
                        onChange={(e) =>
                          updateDetail(index, {
                            additional_requirements: e.target.value,
                          })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={row.rate}
                        onChange={(e) =>
                          updateDetail(index, { rate: e.target.value })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={row.qty}
                        onChange={(e) =>
                          updateDetail(index, { qty: e.target.value })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={row.extra_charge}
                        onChange={(e) =>
                          updateDetail(index, { extra_charge: e.target.value })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={row.discount}
                        onChange={(e) =>
                          updateDetail(index, { discount: e.target.value })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top whitespace-nowrap text-slate-700">
                      {finalRate(row).toFixed(2)}
                    </td>
                    <td className="px-2 py-2 align-top">
                      <input
                        type="text"
                        maxLength={500}
                        value={row.remarks}
                        onChange={(e) =>
                          updateDetail(index, { remarks: e.target.value })
                        }
                        className={compactClass}
                      />
                    </td>
                    <td className="px-2 py-2 align-top text-right whitespace-nowrap">
                      {row.scheduler_detail_id ? (
                        <button
                          type="button"
                          onClick={() =>
                            setCaseRow({
                              detailId: row.scheduler_detail_id,
                              workNo: row.work_no || padWorkNo(mdoCode, index + 1),
                            })
                          }
                          className="mr-2 rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-white"
                        >
                          {row.has_case
                            ? row.case_approval_status === "Approved"
                              ? "View Case"
                              : "Update"
                            : "Case Study"}
                        </button>
                      ) : null}
                      <button
                        type="button"
                        disabled={details.length === 1}
                        onClick={() =>
                          setDetails((prev) =>
                            prev.filter((_, rowIndex) => rowIndex !== index),
                          )
                        }
                        className="rounded-md border border-red-200 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {saving ? "Saving..." : editingId ? "Update" : "Save"}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {editingId && caseRow && (
        <SchedulerCasePanel
          schedulerId={editingId}
          detailId={caseRow.detailId}
          workNo={caseRow.workNo}
          onClose={() => setCaseRow(null)}
          onSaved={() => {
            setDetails((prev) =>
              prev.map((row) =>
                row.scheduler_detail_id === caseRow.detailId
                  ? { ...row, has_case: true }
                  : row,
              ),
            )
            load(search)
          }}
        />
      )}

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-medium text-slate-800">Scheduler List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by MdoCode, customer, patient"
              className="w-80 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            />
            <button
              type="submit"
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Search
            </button>
            <button
              type="button"
              onClick={() => {
                setSearch("")
                load("")
              }}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Reset
            </button>
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  MdoCode
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Customer Name
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Billing Party
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Work Type
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Received
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Completion
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Works
                </th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                    No schedulers found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.scheduler_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.mdo_code}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.customer_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.billing_party_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{item.work_type}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {String(item.work_received_date || "").slice(0, 10)}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {String(item.completion_date || "").slice(0, 10)}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {(item.details || []).length}
                    </td>
                    <td className="px-3 py-2 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => onEdit(item)}
                        className="mr-2 rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-white"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(item.scheduler_id, item.mdo_code)}
                        className="rounded-md border border-red-200 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
