import { useEffect, useMemo, useState } from "react"
import { createBranch, deleteBranch, listBranches, updateBranch } from "../api/branches"
import { listBranchTypes } from "../api/branchTypes"
import { listCompanies } from "../api/companies"
import { listCountries } from "../api/countries"
import { listDistributions } from "../api/distributions"
import { listPlaces } from "../api/places"
import { listRegions } from "../api/regions"
import { listStates } from "../api/states"

const emptyForm = {
  parent_company_id: "",
  branch_type_id: "",
  branch_name: "",
  address1: "",
  address2: "",
  place_id: "",
  pin: "",
  state_id: "",
  country_id: "",
  phone: "",
  mobile: "",
  email: "",
  whatsapp_no: "",
  gst_no: "",
  distribution_id: "",
  iso_number: "",
  ie_code: "",
  status: true,
}

export default function BranchMaster() {
  const [items, setItems] = useState([])
  const [companies, setCompanies] = useState([])
  const [branchTypes, setBranchTypes] = useState([])
  const [countries, setCountries] = useState([])
  const [states, setStates] = useState([])
  const [regions, setRegions] = useState([])
  const [places, setPlaces] = useState([])
  const [distributions, setDistributions] = useState([])
  const [search, setSearch] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  const filteredStates = useMemo(
    () =>
      states.filter(
        (item) =>
          (item.status === "Active" || String(item.state_id) === String(form.state_id)) &&
          (!form.country_id || String(item.country_id) === String(form.country_id)),
      ),
    [states, form.country_id, form.state_id],
  )

  const filteredPlaces = useMemo(() => {
    const regionIds = new Set(
      regions
        .filter(
          (item) =>
            !form.state_id || String(item.state_id) === String(form.state_id),
        )
        .map((item) => String(item.region_id)),
    )
    return places.filter(
      (item) =>
        (item.status === "Active" || String(item.place_id) === String(form.place_id)) &&
        (!form.state_id || regionIds.has(String(item.region_id))),
    )
  }, [places, regions, form.state_id, form.place_id])

  const filteredCompanies = useMemo(
    () =>
      companies.filter(
        (item) =>
          item.status === "Active" ||
          String(item.company_id) === String(form.parent_company_id),
      ),
    [companies, form.parent_company_id],
  )

  const filteredBranchTypes = useMemo(
    () =>
      branchTypes.filter(
        (item) =>
          item.status === "Active" ||
          String(item.branch_type_id) === String(form.branch_type_id),
      ),
    [branchTypes, form.branch_type_id],
  )

  const filteredDistributions = useMemo(
    () =>
      distributions.filter(
        (item) =>
          (item.status === "Active" ||
            String(item.distribution_id) === String(form.distribution_id)) &&
          (!form.parent_company_id ||
            String(item.company_id) === String(form.parent_company_id)),
      ),
    [distributions, form.parent_company_id, form.distribution_id],
  )

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listBranches(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadLookups() {
    try {
      const [
        companyData,
        branchTypeData,
        countryData,
        stateData,
        regionData,
        placeData,
        distributionData,
      ] = await Promise.all([
        listCompanies(""),
        listBranchTypes(""),
        listCountries(""),
        listStates(""),
        listRegions(""),
        listPlaces(""),
        listDistributions(""),
      ])
      setCompanies(companyData)
      setBranchTypes(branchTypeData)
      setCountries(countryData.filter((item) => item.status === "Active"))
      setStates(stateData)
      setRegions(regionData)
      setPlaces(placeData)
      setDistributions(distributionData)
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
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.branch_id)
    setForm({
      parent_company_id: String(item.parent_company_id || ""),
      branch_type_id: String(item.branch_type_id || ""),
      branch_name: item.branch_name || "",
      address1: item.address1 || "",
      address2: item.address2 || "",
      place_id: String(item.place_id || ""),
      pin: item.pin || "",
      state_id: String(item.state_id || ""),
      country_id: String(item.country_id || ""),
      phone: item.phone || "",
      mobile: item.mobile || "",
      email: item.email || "",
      whatsapp_no: item.whatsapp_no || "",
      gst_no: item.gst_no || "",
      distribution_id: item.distribution_id ? String(item.distribution_id) : "",
      iso_number: item.iso_number || "",
      ie_code: item.ie_code || "",
      status: item.status === "Active",
    })
    setMessage("")
    setError("")
  }

  async function onSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")

    const payload = {
      parent_company_id: Number(form.parent_company_id),
      branch_type_id: Number(form.branch_type_id),
      branch_name: form.branch_name.trim(),
      address1: form.address1.trim(),
      address2: form.address2.trim() || null,
      place_id: Number(form.place_id),
      pin: form.pin.trim(),
      state_id: Number(form.state_id),
      country_id: Number(form.country_id),
      phone: form.phone.trim() || null,
      mobile: form.mobile.trim() || null,
      email: form.email.trim() || null,
      whatsapp_no: form.whatsapp_no.trim() || null,
      gst_no: form.gst_no.trim() || null,
      distribution_id: form.distribution_id ? Number(form.distribution_id) : null,
      iso_number: form.iso_number.trim() || null,
      ie_code: form.ie_code.trim() || null,
      status: form.status ? "Active" : "Inactive",
    }

    try {
      if (editingId) {
        await updateBranch(editingId, payload)
        setMessage("Branch updated successfully.")
      } else {
        await createBranch(payload)
        setMessage("Branch created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(branchId, branchName) {
    const confirmed = window.confirm(
      `Delete branch "${branchName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteBranch(branchId)
      if (editingId === branchId) {
        resetForm()
      }
      setMessage("Branch deleted successfully.")
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

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Branch Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete branches.
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

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-lg font-medium text-slate-800">
          {editingId ? "Edit Branch" : "Create Branch"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Parent Company</span>
            <select
              required
              value={form.parent_company_id}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  parent_company_id: e.target.value,
                  distribution_id: "",
                }))
              }
              className={inputClass}
            >
              <option value="">Select parent company</option>
              {filteredCompanies.map((item) => (
                <option key={item.company_id} value={item.company_id}>
                  {item.company_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Branch Type</span>
            <select
              required
              value={form.branch_type_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, branch_type_id: e.target.value }))
              }
              className={inputClass}
            >
              <option value="">Select branch type</option>
              {filteredBranchTypes.map((item) => (
                <option key={item.branch_type_id} value={item.branch_type_id}>
                  {item.branch_type_name}
                </option>
              ))}
            </select>
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

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Branch Name</span>
            <input
              type="text"
              required
              maxLength={150}
              value={form.branch_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, branch_name: e.target.value }))
              }
              className={inputClass}
              placeholder="e.g. Kochi Branch"
            />
          </label>

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Address1</span>
            <input
              type="text"
              required
              maxLength={255}
              value={form.address1}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, address1: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Address2</span>
            <input
              type="text"
              maxLength={255}
              value={form.address2}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, address2: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Country</span>
            <select
              required
              value={form.country_id}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  country_id: e.target.value,
                  state_id: "",
                  place_id: "",
                }))
              }
              className={inputClass}
            >
              <option value="">Select country</option>
              {countries.map((item) => (
                <option key={item.country_id} value={item.country_id}>
                  {item.country_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">State</span>
            <select
              required
              value={form.state_id}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  state_id: e.target.value,
                  place_id: "",
                }))
              }
              className={inputClass}
            >
              <option value="">Select state</option>
              {filteredStates.map((item) => (
                <option key={item.state_id} value={item.state_id}>
                  {item.state_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Place</span>
            <select
              required
              value={form.place_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, place_id: e.target.value }))
              }
              className={inputClass}
            >
              <option value="">Select place</option>
              {filteredPlaces.map((item) => (
                <option key={item.place_id} value={item.place_id}>
                  {item.place_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Pin</span>
            <input
              type="text"
              required
              maxLength={20}
              value={form.pin}
              onChange={(e) => setForm((prev) => ({ ...prev, pin: e.target.value }))}
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Phone</span>
            <input
              type="text"
              maxLength={30}
              value={form.phone}
              onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))}
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Mobile</span>
            <input
              type="text"
              maxLength={30}
              value={form.mobile}
              onChange={(e) => setForm((prev) => ({ ...prev, mobile: e.target.value }))}
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Email</span>
            <input
              type="email"
              maxLength={150}
              value={form.email}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">WhatsApp No</span>
            <input
              type="text"
              maxLength={30}
              value={form.whatsapp_no}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, whatsapp_no: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">GST No</span>
            <input
              type="text"
              maxLength={50}
              value={form.gst_no}
              onChange={(e) => setForm((prev) => ({ ...prev, gst_no: e.target.value }))}
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">
              Distribution Code
            </span>
            <select
              value={form.distribution_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, distribution_id: e.target.value }))
              }
              className={inputClass}
            >
              <option value="">Select distribution</option>
              {filteredDistributions.map((item) => (
                <option key={item.distribution_id} value={item.distribution_id}>
                  {item.distribution_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">ISO Number</span>
            <input
              type="text"
              maxLength={50}
              value={form.iso_number}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, iso_number: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">IE Code</span>
            <input
              type="text"
              maxLength={50}
              value={form.ie_code}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, ie_code: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <div className="md:col-span-3 flex gap-2">
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
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-medium text-slate-800">Branch List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, company, GST"
              className="w-72 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
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
                  Branch Name
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Parent Company
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Branch Type
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Place</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Mobile
                </th>
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
                    No branches found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.branch_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.branch_name}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.parent_company_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.branch_type_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{item.place_name || "-"}</td>
                    <td className="px-3 py-2 text-slate-700">{item.mobile || "-"}</td>
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
                        onClick={() => onDelete(item.branch_id, item.branch_name)}
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
