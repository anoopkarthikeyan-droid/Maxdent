import { useEffect, useMemo, useState } from "react"
import { listBranches } from "../api/branches"
import { listCountries } from "../api/countries"
import {
  createCustomer,
  deleteCustomer,
  listCustomers,
  updateCustomer,
} from "../api/customers"
import { listCurrencies } from "../api/currencies"
import { listDistributions } from "../api/distributions"
import { listPlaces } from "../api/places"
import { listRegions } from "../api/regions"
import { listRoutes } from "../api/routes"
import { listStates } from "../api/states"

const emptyForm = {
  branch_name: "",
  contact_person: "",
  address: "",
  address1: "",
  place_id: "",
  route_id: "",
  region_id: "",
  state_id: "",
  country_id: "",
  currency_id: "",
  distribution_id: "",
  linked_branch_id: "",
  gst_no: "",
  phone: "",
  mobile: "",
  email: "",
  whatsapp_no: "",
  current_balance: "0",
  inclusive_tax: false,
  remarks: "",
  head_office_id: "",
  billing_office_id: "",
}

export default function CustomerMaster() {
  const [items, setItems] = useState([])
  const [officeCustomers, setOfficeCustomers] = useState([])
  const [branches, setBranches] = useState([])
  const [countries, setCountries] = useState([])
  const [states, setStates] = useState([])
  const [regions, setRegions] = useState([])
  const [routes, setRoutes] = useState([])
  const [places, setPlaces] = useState([])
  const [currencies, setCurrencies] = useState([])
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

  const filteredRegions = useMemo(
    () =>
      regions.filter(
        (item) =>
          (item.status === "Active" ||
            String(item.region_id) === String(form.region_id)) &&
          (!form.state_id || String(item.state_id) === String(form.state_id)),
      ),
    [regions, form.state_id, form.region_id],
  )

  const filteredPlaces = useMemo(
    () =>
      places.filter(
        (item) =>
          (item.status === "Active" || String(item.place_id) === String(form.place_id)) &&
          (!form.region_id || String(item.region_id) === String(form.region_id)),
      ),
    [places, form.region_id, form.place_id],
  )

  const filteredRoutes = useMemo(
    () =>
      routes.filter(
        (item) =>
          (item.status === "Active" || String(item.route_id) === String(form.route_id)) &&
          (!form.region_id || String(item.region_id) === String(form.region_id)),
      ),
    [routes, form.region_id, form.route_id],
  )

  const filteredBranches = useMemo(
    () =>
      branches.filter(
        (item) =>
          item.status === "Active" ||
          String(item.branch_id) === String(form.linked_branch_id),
      ),
    [branches, form.linked_branch_id],
  )

  const filteredCurrencies = useMemo(
    () =>
      currencies.filter(
        (item) =>
          item.status === "Active" ||
          String(item.currency_id) === String(form.currency_id),
      ),
    [currencies, form.currency_id],
  )

  const selectedLinkedBranch = useMemo(
    () =>
      branches.find(
        (item) => String(item.branch_id) === String(form.linked_branch_id),
      ),
    [branches, form.linked_branch_id],
  )

  const filteredDistributions = useMemo(
    () =>
      distributions.filter(
        (item) =>
          (item.status === "Active" ||
            String(item.distribution_id) === String(form.distribution_id)) &&
          (!selectedLinkedBranch ||
            String(item.company_id) === String(selectedLinkedBranch.parent_company_id)),
      ),
    [distributions, selectedLinkedBranch, form.distribution_id],
  )

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listCustomers(searchTerm)
      setItems(data)
      const officeData = searchTerm ? await listCustomers("") : data
      setOfficeCustomers(officeData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadLookups() {
    try {
      const [
        branchData,
        countryData,
        stateData,
        regionData,
        routeData,
        placeData,
        currencyData,
        distributionData,
      ] = await Promise.all([
        listBranches(""),
        listCountries(""),
        listStates(""),
        listRegions(""),
        listRoutes(""),
        listPlaces(""),
        listCurrencies(""),
        listDistributions(""),
      ])
      setBranches(branchData)
      setCountries(countryData.filter((item) => item.status === "Active"))
      setStates(stateData)
      setRegions(regionData)
      setRoutes(routeData)
      setPlaces(placeData)
      setCurrencies(currencyData)
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
    setEditingId(item.customer_id)
    setForm({
      branch_name: item.branch_name || "",
      contact_person: item.contact_person || "",
      address: item.address || "",
      address1: item.address1 || "",
      place_id: String(item.place_id || ""),
      route_id: String(item.route_id || ""),
      region_id: String(item.region_id || ""),
      state_id: String(item.state_id || ""),
      country_id: String(item.country_id || ""),
      currency_id: String(item.currency_id || ""),
      distribution_id: String(item.distribution_id || ""),
      linked_branch_id: String(item.linked_branch_id || ""),
      gst_no: item.gst_no || "",
      phone: item.phone || "",
      mobile: item.mobile || "",
      email: item.email || "",
      whatsapp_no: item.whatsapp_no || "",
      current_balance:
        item.current_balance === null || item.current_balance === undefined
          ? "0"
          : String(item.current_balance),
      inclusive_tax: Boolean(item.inclusive_tax),
      remarks: item.remarks || "",
      head_office_id: item.head_office_id ? String(item.head_office_id) : "",
      billing_office_id: item.billing_office_id ? String(item.billing_office_id) : "",
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
      branch_name: form.branch_name.trim(),
      contact_person: form.contact_person.trim() || null,
      address: form.address.trim(),
      address1: form.address1.trim() || null,
      place_id: Number(form.place_id),
      route_id: Number(form.route_id),
      region_id: Number(form.region_id),
      state_id: Number(form.state_id),
      country_id: Number(form.country_id),
      currency_id: Number(form.currency_id),
      distribution_id: Number(form.distribution_id),
      linked_branch_id: Number(form.linked_branch_id),
      gst_no: form.gst_no.trim() || null,
      phone: form.phone.trim() || null,
      mobile: form.mobile.trim() || null,
      email: form.email.trim() || null,
      whatsapp_no: form.whatsapp_no.trim() || null,
      current_balance: Number(form.current_balance || 0),
      inclusive_tax: Boolean(form.inclusive_tax),
      remarks: form.remarks.trim() || null,
    }

    if (editingId) {
      payload.head_office_id = form.head_office_id ? Number(form.head_office_id) : null
      payload.billing_office_id = form.billing_office_id
        ? Number(form.billing_office_id)
        : null
    }

    try {
      if (editingId) {
        await updateCustomer(editingId, payload)
        setMessage("Customer updated successfully.")
      } else {
        await createCustomer(payload)
        setMessage("Customer created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(customerId, branchName) {
    const confirmed = window.confirm(
      `Delete customer "${branchName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteCustomer(customerId)
      if (editingId === customerId) {
        resetForm()
      }
      setMessage("Customer deleted successfully.")
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
        <h1 className="text-2xl font-semibold text-slate-900">Customer Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete customers.
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
          {editingId ? "Edit Customer" : "Create Customer"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm md:col-span-2">
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
              placeholder="e.g. Smile Dental Clinic"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Contact Person</span>
            <input
              type="text"
              maxLength={150}
              value={form.contact_person}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, contact_person: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Address</span>
            <input
              type="text"
              required
              maxLength={255}
              value={form.address}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, address: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Address1</span>
            <input
              type="text"
              maxLength={255}
              value={form.address1}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, address1: e.target.value }))
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
                  route_id: "",
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
                  route_id: "",
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
                  route_id: "",
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
            <span className="mb-1 block font-medium text-slate-700">Route</span>
            <select
              required
              value={form.route_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, route_id: e.target.value }))
              }
              className={inputClass}
            >
              <option value="">Select route</option>
              {filteredRoutes.map((item) => (
                <option key={item.route_id} value={item.route_id}>
                  {item.route_code}
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
              {filteredCurrencies.map((item) => (
                <option key={item.currency_id} value={item.currency_id}>
                  {item.currency_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Linked Branch</span>
            <select
              required
              value={form.linked_branch_id}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  linked_branch_id: e.target.value,
                  distribution_id: "",
                }))
              }
              className={inputClass}
            >
              <option value="">Select linked branch</option>
              {filteredBranches.map((item) => (
                <option key={item.branch_id} value={item.branch_id}>
                  {item.branch_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Distribution</span>
            <select
              required
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
            <span className="mb-1 block font-medium text-slate-700">GST</span>
            <input
              type="text"
              maxLength={50}
              value={form.gst_no}
              onChange={(e) => setForm((prev) => ({ ...prev, gst_no: e.target.value }))}
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
            <span className="mb-1 block font-medium text-slate-700">WhatsApp</span>
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
            <span className="mb-1 block font-medium text-slate-700">
              Current Balance
            </span>
            <input
              type="number"
              step="0.01"
              value={form.current_balance}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, current_balance: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="flex items-end gap-2 pb-2 text-sm">
            <input
              type="checkbox"
              checked={Boolean(form.inclusive_tax)}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, inclusive_tax: e.target.checked }))
              }
              className="h-4 w-4 rounded border-slate-300"
            />
            <span className="font-medium text-slate-700">Inclusive Tax</span>
          </label>

          <label className="block text-sm md:col-span-3">
            <span className="mb-1 block font-medium text-slate-700">Remarks</span>
            <textarea
              maxLength={500}
              rows={3}
              value={form.remarks}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, remarks: e.target.value }))
              }
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Head Office</span>
            <select
              disabled={!editingId}
              value={form.head_office_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, head_office_id: e.target.value }))
              }
              className={`${inputClass} disabled:bg-slate-100 disabled:text-slate-500`}
            >
              <option value="">Select head office</option>
              {officeCustomers
                .slice()
                .sort((a, b) => a.branch_name.localeCompare(b.branch_name))
                .map((item) => (
                  <option key={`ho-${item.customer_id}`} value={item.customer_id}>
                    {item.branch_name}
                  </option>
                ))}
            </select>
            {!editingId && (
              <span className="mt-1 block text-xs text-slate-500">
                Left blank on save. Set this after creating the customer.
              </span>
            )}
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Billing Office</span>
            <select
              disabled={!editingId}
              value={form.billing_office_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, billing_office_id: e.target.value }))
              }
              className={`${inputClass} disabled:bg-slate-100 disabled:text-slate-500`}
            >
              <option value="">Select billing office</option>
              {officeCustomers
                .slice()
                .sort((a, b) => a.branch_name.localeCompare(b.branch_name))
                .map((item) => (
                  <option key={`bo-${item.customer_id}`} value={item.customer_id}>
                    {item.branch_name}
                  </option>
                ))}
            </select>
            {!editingId && (
              <span className="mt-1 block text-xs text-slate-500">
                Left blank on save. Set this after creating the customer.
              </span>
            )}
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
          <h2 className="text-lg font-medium text-slate-800">Customer List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, contact, GST"
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
                  Contact Person
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Place</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Linked Branch
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Mobile
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Current Balance
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Head Office
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Billing Office
                </th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-3 py-6 text-center text-slate-500">
                    No customers found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.customer_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.branch_name}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.contact_person || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{item.place_name || "-"}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.linked_branch_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{item.mobile || "-"}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {Number(item.current_balance || 0).toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.head_office_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.billing_office_name || "-"}
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
                        onClick={() => onDelete(item.customer_id, item.branch_name)}
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
