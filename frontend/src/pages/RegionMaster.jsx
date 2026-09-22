import { useEffect, useState } from "react"
import {
  createRegion,
  deleteRegion,
  listRegions,
  updateRegion,
} from "../api/regions"
import { listStates } from "../api/states"

const emptyForm = {
  region_name: "",
  state_id: "",
  status: "Active",
}

export default function RegionMaster() {
  const [items, setItems] = useState([])
  const [states, setStates] = useState([])
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
      const data = await listRegions(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadStates() {
    try {
      const data = await listStates("")
      setStates(data.filter((item) => item.status === "Active"))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load("")
    loadStates()
  }, [])

  function resetForm() {
    setForm(emptyForm)
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.region_id)
    setForm({
      region_name: item.region_name,
      state_id: String(item.state_id),
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
      region_name: form.region_name.trim(),
      state_id: Number(form.state_id),
      status: form.status,
    }

    try {
      if (editingId) {
        await updateRegion(editingId, payload)
        setMessage("Region updated successfully.")
      } else {
        await createRegion(payload)
        setMessage("Region created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(regionId, regionName) {
    const confirmed = window.confirm(
      `Delete region "${regionName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteRegion(regionId)
      if (editingId === regionId) {
        resetForm()
      }
      setMessage("Region deleted successfully.")
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
        <h1 className="text-2xl font-semibold text-slate-900">Region Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete regions.
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
          {editingId ? "Edit Region" : "Create Region"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Region</span>
            <input
              type="text"
              required
              maxLength={100}
              value={form.region_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, region_name: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. North"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">State</span>
            <select
              required
              value={form.state_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, state_id: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
            >
              <option value="">Select state</option>
              {states.map((state) => (
                <option key={state.state_id} value={state.state_id}>
                  {state.state_name}
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
          <h2 className="text-lg font-medium text-slate-800">Region List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by region or state"
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
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Region</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">State</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Status</th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                    No regions found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.region_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.region_name}</td>
                    <td className="px-3 py-2 text-slate-700">{item.state_name || "-"}</td>
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
                        onClick={() => onDelete(item.region_id, item.region_name)}
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
