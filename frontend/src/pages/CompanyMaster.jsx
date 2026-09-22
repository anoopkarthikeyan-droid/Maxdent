import { useEffect, useMemo, useState } from "react"
import {
  createCompany,
  deleteCompany,
  listCompanies,
  updateCompany,
} from "../api/companies"
import { listCountries } from "../api/countries"
import { listPlaces } from "../api/places"
import { listRegions } from "../api/regions"
import { listStates } from "../api/states"

const emptyForm = {
  company_name: "",
  company_code: "",
  address: "",
  address2: "",
  place_id: "",
  region_id: "",
  state_id: "",
  country_id: "",
  pin: "",
  phone: "",
  mobile: "",
  email: "",
  whatsapp_no: "",
  gst_no: "",
  ie_code: "",
  iso_number: "",
  status: "Active",
}

export default function CompanyMaster() {
  const [items, setItems] = useState([])
  const [countries, setCountries] = useState([])
  const [states, setStates] = useState([])
  const [regions, setRegions] = useState([])
  const [places, setPlaces] = useState([])
  const [search, setSearch] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState("")
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  const filteredStates = useMemo(
    () =>
      states.filter(
        (item) =>
          item.status === "Active" &&
          (!form.country_id || String(item.country_id) === String(form.country_id)),
      ),
    [states, form.country_id],
  )

  const filteredRegions = useMemo(
    () =>
      regions.filter(
        (item) =>
          item.status === "Active" &&
          (!form.state_id || String(item.state_id) === String(form.state_id)),
      ),
    [regions, form.state_id],
  )

  const filteredPlaces = useMemo(
    () =>
      places.filter(
        (item) =>
          item.status === "Active" &&
          (!form.region_id || String(item.region_id) === String(form.region_id)),
      ),
    [places, form.region_id],
  )

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listCompanies(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadLookups() {
    try {
      const [countryData, stateData, regionData, placeData] = await Promise.all([
        listCountries(""),
        listStates(""),
        listRegions(""),
        listPlaces(""),
      ])
      setCountries(countryData.filter((item) => item.status === "Active"))
      setStates(stateData)
      setRegions(regionData)
      setPlaces(placeData)
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
    setLogoFile(null)
    setLogoPreview("")
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.company_id)
    setForm({
      company_name: item.company_name || "",
      company_code: item.company_code || "",
      address: item.address || "",
      address2: item.address2 || "",
      place_id: String(item.place_id || ""),
      region_id: String(item.region_id || ""),
      state_id: String(item.state_id || ""),
      country_id: String(item.country_id || ""),
      pin: item.pin || "",
      phone: item.phone || "",
      mobile: item.mobile || "",
      email: item.email || "",
      whatsapp_no: item.whatsapp_no || "",
      gst_no: item.gst_no || "",
      ie_code: item.ie_code || "",
      iso_number: item.iso_number || "",
      status: item.status || "Active",
    })
    setLogoFile(null)
    setLogoPreview(item.logo_path || "")
    setMessage("")
    setError("")
  }

  function onLogoChange(event) {
    const file = event.target.files?.[0] || null
    setLogoFile(file)
    if (file) {
      setLogoPreview(URL.createObjectURL(file))
    }
  }

  function buildFormData() {
    const data = new FormData()
    Object.entries(form).forEach(([key, value]) => {
      data.append(key, value ?? "")
    })
    if (logoFile) {
      data.append("logo", logoFile)
    }
    return data
  }

  async function onSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")

    try {
      const payload = buildFormData()
      if (editingId) {
        await updateCompany(editingId, payload)
        setMessage("Company updated successfully.")
      } else {
        await createCompany(payload)
        setMessage("Company created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(companyId, companyName) {
    const confirmed = window.confirm(
      `Delete company "${companyName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteCompany(companyId)
      if (editingId === companyId) {
        resetForm()
      }
      setMessage("Company deleted successfully.")
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
        <h1 className="text-2xl font-semibold text-slate-900">Company Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete companies.
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
          {editingId ? "Edit Company" : "Create Company"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Name</span>
            <input
              type="text"
              required
              maxLength={150}
              value={form.company_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, company_name: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Company Code</span>
            <input
              type="text"
              required
              maxLength={50}
              value={form.company_code}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  company_code: e.target.value.toUpperCase(),
                }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Status</span>
            <select
              value={form.status}
              onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
              className={inputClass}
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </label>

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Address</span>
            <input
              type="text"
              required
              maxLength={255}
              value={form.address}
              onChange={(e) => setForm((prev) => ({ ...prev, address: e.target.value }))}
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
                  region_id: "",
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
                  region_id: "",
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
            <span className="mb-1 block font-medium text-slate-700">Region</span>
            <select
              required
              value={form.region_id}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  region_id: e.target.value,
                  place_id: "",
                }))
              }
              className={inputClass}
            >
              <option value="">Select region</option>
              {filteredRegions.map((item) => (
                <option key={item.region_id} value={item.region_id}>
                  {item.region_name}
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
            <span className="mb-1 block font-medium text-slate-700">IE Code</span>
            <input
              type="text"
              maxLength={50}
              value={form.ie_code}
              onChange={(e) => setForm((prev) => ({ ...prev, ie_code: e.target.value }))}
              className={inputClass}
            />
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

          <label className="block text-sm md:col-span-2">
            <span className="mb-1 block font-medium text-slate-700">Logo</span>
            <input
              type="file"
              accept="image/*"
              onChange={onLogoChange}
              className="w-full text-sm text-slate-700"
            />
          </label>

          {logoPreview && (
            <div className="flex items-end">
              <img
                src={logoPreview}
                alt="Company logo preview"
                className="h-16 w-16 rounded border border-slate-200 object-contain bg-white"
              />
            </div>
          )}

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
          <h2 className="text-lg font-medium text-slate-800">Company List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, code, email, GST"
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
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Logo</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Name</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Code</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Place</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Country
                </th>
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
                  <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                    No companies found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.company_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2">
                      {item.logo_path ? (
                        <img
                          src={item.logo_path}
                          alt=""
                          className="h-10 w-10 rounded border border-slate-200 object-contain bg-white"
                        />
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{item.company_name}</td>
                    <td className="px-3 py-2 font-medium text-slate-900">
                      {item.company_code}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.place_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.country_name || "-"}
                    </td>
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
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => onEdit(item)}
                        className="mr-2 rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-white"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(item.company_id, item.company_name)}
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
