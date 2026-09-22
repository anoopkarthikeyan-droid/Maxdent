import { useEffect, useMemo, useState } from "react"
import { listCompanies } from "../api/companies"
import { listCurrencies } from "../api/currencies"
import {
  createDistribution,
  deleteDistribution,
  listDistributions,
  updateDistribution,
} from "../api/distributions"
import { listSections } from "../api/sections"
import { listWorks } from "../api/works"

const emptyForm = {
  distribution_name: "",
  section_id: "",
  currency_id: "",
  company_id: "",
  effective_from: "",
  effective_to: "",
  status: true,
}

const emptyRates = {
  prime_rate: "",
  supreme_rate: "",
  supreme_plus_rate: "",
  collection_charge: "",
  collection_percentage: "",
}

const PAGE_SIZES = [50, 100, "all"]

function toNumber(value) {
  if (value === "" || value === null || value === undefined) return 0
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function ratesFromSaved(details = []) {
  const next = {}
  for (const detail of details) {
    next[detail.work_id] = {
      prime_rate: String(detail.prime_rate ?? ""),
      supreme_rate: String(detail.supreme_rate ?? ""),
      supreme_plus_rate: String(detail.supreme_plus_rate ?? ""),
      collection_charge: String(detail.collection_charge ?? ""),
      collection_percentage: String(detail.collection_percentage ?? ""),
    }
  }
  return next
}

export default function DistributionMaster() {
  const [items, setItems] = useState([])
  const [sections, setSections] = useState([])
  const [currencies, setCurrencies] = useState([])
  const [companies, setCompanies] = useState([])
  const [works, setWorks] = useState([])
  const [search, setSearch] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [rates, setRates] = useState({})
  const [pageSize, setPageSize] = useState(50)
  const [page, setPage] = useState(1)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  const detailWorks = useMemo(() => {
    if (!form.section_id) return []
    const sectionWorks = works.filter(
      (work) => String(work.section_id) === String(form.section_id),
    )
    const byId = new Map(sectionWorks.map((work) => [work.work_id, work]))
    const extra = Object.keys(rates)
      .map((id) => Number(id))
      .filter((id) => !byId.has(id))
      .map((id) => works.find((work) => work.work_id === id))
      .filter(
        (work) => work && String(work.section_id) === String(form.section_id),
      )
    return [...sectionWorks, ...extra]
  }, [works, rates, form.section_id])

  const totalPages =
    pageSize === "all" || detailWorks.length === 0
      ? 1
      : Math.max(1, Math.ceil(detailWorks.length / pageSize))
  const currentPage = Math.min(page, totalPages)
  const pagedWorks =
    pageSize === "all"
      ? detailWorks
      : detailWorks.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  const rangeStart = detailWorks.length === 0 ? 0 : pageSize === "all" ? 1 : (currentPage - 1) * pageSize + 1
  const rangeEnd =
    pageSize === "all" ? detailWorks.length : Math.min(currentPage * pageSize, detailWorks.length)

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listDistributions(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadLookups() {
    try {
      const [sectionData, currencyData, companyData, workData] = await Promise.all([
        listSections(""),
        listCurrencies(""),
        listCompanies(""),
        listWorks(""),
      ])
      setSections(sectionData.filter((item) => item.status === "Active"))
      setCurrencies(currencyData.filter((item) => item.status === "Active"))
      setCompanies(companyData.filter((item) => item.status === "Active"))
      setWorks(workData)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load("")
    loadLookups()
  }, [])

  function resetForm() {
    setForm(emptyForm)
    setRates({})
    setPage(1)
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.distribution_id)
    setForm({
      distribution_name: item.distribution_name,
      section_id: String(item.section_id),
      currency_id: String(item.currency_id),
      company_id: String(item.company_id),
      effective_from: item.effective_from,
      effective_to: item.effective_to,
      status: item.status === "Active",
    })
    setRates(ratesFromSaved(item.details || []))
    setPage(1)
    setMessage("")
    setError("")
  }

  function updateRate(workId, field, value) {
    setRates((prev) => ({
      ...prev,
      [workId]: {
        ...(prev[workId] || emptyRates),
        [field]: value,
      },
    }))
  }

  function changePageSize(size) {
    setPageSize(size)
    setPage(1)
  }

  async function onSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")

    const payloadDetails = detailWorks.map((work) => {
      const row = rates[work.work_id] || emptyRates
      return {
        work_id: Number(work.work_id),
        prime_rate: toNumber(row.prime_rate),
        supreme_rate: toNumber(row.supreme_rate),
        supreme_plus_rate: toNumber(row.supreme_plus_rate),
        collection_charge: toNumber(row.collection_charge),
        collection_percentage: toNumber(row.collection_percentage),
      }
    })

    const payload = {
      distribution_name: form.distribution_name.trim(),
      section_id: Number(form.section_id),
      currency_id: Number(form.currency_id),
      company_id: Number(form.company_id),
      effective_from: form.effective_from,
      effective_to: form.effective_to,
      status: form.status ? "Active" : "Inactive",
      details: payloadDetails,
    }

    try {
      if (editingId) {
        await updateDistribution(editingId, payload)
        setMessage("Distribution updated successfully.")
      } else {
        await createDistribution(payload)
        setMessage("Distribution created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(distributionId, distributionName) {
    const confirmed = window.confirm(
      `Delete distribution "${distributionName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteDistribution(distributionId)
      if (editingId === distributionId) {
        resetForm()
      }
      setMessage("Distribution deleted successfully.")
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
  const detailInputClass =
    "w-full min-w-[6rem] rounded-md border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-slate-500"

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Distribution Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete distributions with work rates.
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
            {editingId ? "Edit Distribution" : "Create Distribution"}
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block text-sm md:col-span-2">
              <span className="mb-1 block font-medium text-slate-700">
                Distribution Name
              </span>
              <input
                type="text"
                required
                maxLength={150}
                value={form.distribution_name}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, distribution_name: e.target.value }))
                }
                className={inputClass}
                placeholder="e.g. South Zone Rates"
              />
            </label>

            <label className="flex items-end gap-2 pb-2 text-sm">
              <input
                type="checkbox"
                checked={Boolean(form.status)}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, status: e.target.checked }))
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              <span className="font-medium text-slate-700">Status</span>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Section</span>
              <select
                required
                value={form.section_id}
                onChange={(e) => {
                  setForm((prev) => ({ ...prev, section_id: e.target.value }))
                  setPage(1)
                }}
                className={inputClass}
              >
                <option value="">Select section</option>
                {sections.map((section) => (
                  <option key={section.section_id} value={section.section_id}>
                    {section.section_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Currency</span>
              <select
                required
                value={form.currency_id}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, currency_id: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">Select currency</option>
                {currencies.map((currency) => (
                  <option key={currency.currency_id} value={currency.currency_id}>
                    {currency.currency_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Company</span>
              <select
                required
                value={form.company_id}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, company_id: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">Select company</option>
                {companies.map((company) => (
                  <option key={company.company_id} value={company.company_id}>
                    {company.company_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">
                Effective From
              </span>
              <input
                type="date"
                required
                value={form.effective_from}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, effective_from: e.target.value }))
                }
                className={inputClass}
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Effective To</span>
              <input
                type="date"
                required
                value={form.effective_to}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, effective_to: e.target.value }))
                }
                className={inputClass}
              />
            </label>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <h2 className="text-lg font-medium text-slate-800">Detail</h2>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1 text-sm">
                <span className="mr-1 text-slate-600">Show</span>
                {PAGE_SIZES.map((size) => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => changePageSize(size)}
                    className={`rounded-md px-2.5 py-1 text-sm font-medium ${
                      pageSize === size
                        ? "bg-slate-900 text-white"
                        : "border border-slate-300 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {size === "all" ? "All" : size}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2 text-sm">
                <button
                  type="button"
                  disabled={currentPage <= 1}
                  onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                  className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="whitespace-nowrap text-slate-600">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  disabled={currentPage >= totalPages}
                  onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                  className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
          <p className="mb-3 text-sm text-slate-500">
            {!form.section_id
              ? "Select a section to list works."
              : detailWorks.length === 0
                ? "No works found for this section."
                : `Showing ${rangeStart}–${rangeEnd} of ${detailWorks.length} works`}
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">Work</th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Prime Rate
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Supreme Rate
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Supreme Plus Rate
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Collection Charge
                  </th>
                  <th className="px-2 py-2 text-left font-semibold text-slate-700">
                    Collection Percentage
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pagedWorks.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                      {!form.section_id
                        ? "Select a section to list works."
                        : "No works found for this section."}
                    </td>
                  </tr>
                ) : (
                  pagedWorks.map((work) => {
                    const row = rates[work.work_id] || emptyRates
                    return (
                      <tr key={work.work_id} className="hover:bg-slate-50">
                        <td className="px-2 py-2 font-medium text-slate-800">
                          {work.work_name}
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={row.prime_rate}
                            onChange={(e) =>
                              updateRate(work.work_id, "prime_rate", e.target.value)
                            }
                            className={detailInputClass}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={row.supreme_rate}
                            onChange={(e) =>
                              updateRate(work.work_id, "supreme_rate", e.target.value)
                            }
                            className={detailInputClass}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={row.supreme_plus_rate}
                            onChange={(e) =>
                              updateRate(work.work_id, "supreme_plus_rate", e.target.value)
                            }
                            className={detailInputClass}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={row.collection_charge}
                            onChange={(e) =>
                              updateRate(work.work_id, "collection_charge", e.target.value)
                            }
                            className={detailInputClass}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            max="100"
                            step="0.01"
                            value={row.collection_percentage}
                            onChange={(e) =>
                              updateRate(
                                work.work_id,
                                "collection_percentage",
                                e.target.value,
                              )
                            }
                            className={detailInputClass}
                          />
                        </td>
                      </tr>
                    )
                  })
                )}
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

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-medium text-slate-800">Distribution List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Distribution Name"
              className="w-64 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
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
                  Distribution Name
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Section</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Currency</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Company</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Period</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Status</th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                    No distributions found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.distribution_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.distribution_name}</td>
                    <td className="px-3 py-2 text-slate-700">{item.section_name}</td>
                    <td className="px-3 py-2 text-slate-700">{item.currency_name}</td>
                    <td className="px-3 py-2 text-slate-700">{item.company_name}</td>
                    <td className="px-3 py-2 text-slate-700 whitespace-nowrap">
                      {item.effective_from} to {item.effective_to}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          item.status === "Active"
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {item.status}
                      </span>
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
                        onClick={() =>
                          onDelete(item.distribution_id, item.distribution_name)
                        }
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
