import { useEffect, useState } from "react"
import { listCountries } from "../api/countries"
import {
  createState,
  deleteState,
  listStates,
  updateState,
} from "../api/states"

const emptyForm = {
  state_name: "",
  country_id: "",
  cgst_percent: "",
  sgst_percent: "",
  igst_percent: "",
  status: "Active",
}

export default function StateMaster() {
  const [items, setItems] = useState([])
  const [countries, setCountries] = useState([])
  const [search, setSearch] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listStates(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadCountries() {
    try {
      const data = await listCountries("")
      setCountries(data.filter((item) => item.status === "Active"))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load("")
    loadCountries()
  }, [])

  function resetForm() {
    setForm(emptyForm)
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.state_id)
    setForm({
      state_name: item.state_name,
      country_id: String(item.country_id),
      cgst_percent: String(item.cgst_percent),
      sgst_percent: String(item.sgst_percent),
      igst_percent: String(item.igst_percent),
      status: item.status,
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
      state_name: form.state_name.trim(),
      country_id: Number(form.country_id),
      cgst_percent: Number(form.cgst_percent),
      sgst_percent: Number(form.sgst_percent),
      igst_percent: Number(form.igst_percent),
      status: form.status,
    }

    try {
      if (editingId) {
        await updateState(editingId, payload)
        setMessage("State updated successfully.")
      } else {
        await createState(payload)
        setMessage("State created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(stateId, stateName) {
    const confirmed = window.confirm(
      `Delete state "${stateName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteState(stateId)
      if (editingId === stateId) {
        resetForm()
      }
      setMessage("State deleted successfully.")
      await load(search)
    } catch (err) {
      setError(err.message)
    }
  }

  function onSearchSubmit(event) {
    event.preventDefault()
    load(search)
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">State Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete states.
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
          {editingId ? "Edit State" : "Create State"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">State</span>
            <input
              type="text"
              required
              maxLength={100}
              value={form.state_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, state_name: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. California"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Country</span>
            <select
              required
              value={form.country_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, country_id: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="">Select country</option>
              {countries.map((country) => (
                <option key={country.country_id} value={country.country_id}>
                  {country.country_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Status</span>
            <select
              value={form.status}
              onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">CGST %</span>
            <input
              type="number"
              required
              min="0"
              max="100"
              step="0.01"
              value={form.cgst_percent}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, cgst_percent: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. 9"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">SGST %</span>
            <input
              type="number"
              required
              min="0"
              max="100"
              step="0.01"
              value={form.sgst_percent}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, sgst_percent: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. 9"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">IGST %</span>
            <input
              type="number"
              required
              min="0"
              max="100"
              step="0.01"
              value={form.igst_percent}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, igst_percent: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. 18"
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
          <h2 className="text-lg font-medium text-slate-800">State List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by state or country"
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
                <th className="px-3 py-2 text-left font-semibold text-slate-700">State</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Country
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  CGST %
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  SGST %
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  IGST %
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
                    No states found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.state_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.state_name}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.country_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{item.cgst_percent}</td>
                    <td className="px-3 py-2 text-slate-700">{item.sgst_percent}</td>
                    <td className="px-3 py-2 text-slate-700">{item.igst_percent}</td>
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
                        onClick={() => onDelete(item.state_id, item.state_name)}
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
