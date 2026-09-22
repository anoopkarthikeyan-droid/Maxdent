import { useEffect, useState } from "react"
import {
  createBranchType,
  deleteBranchType,
  listBranchTypes,
  updateBranchType,
} from "../api/branchTypes"

const FLAG_FIELDS = [
  { key: "work_collection", label: "Work Collection" },
  { key: "case_study", label: "Case Study" },
  { key: "production", label: "Production" },
  { key: "qc", label: "QC" },
  { key: "billing", label: "Billing" },
  { key: "transportation", label: "Transportation" },
  { key: "payment_collection", label: "Payment Collection" },
]

const emptyForm = {
  branch_type_name: "",
  work_collection: false,
  case_study: false,
  production: false,
  qc: false,
  billing: false,
  transportation: false,
  payment_collection: false,
  status: "Active",
}

export default function BranchTypeMaster() {
  const [items, setItems] = useState([])
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
      const data = await listBranchTypes(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load("")
  }, [])

  function resetForm() {
    setForm(emptyForm)
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.branch_type_id)
    setForm({
      branch_type_name: item.branch_type_name,
      work_collection: Boolean(item.work_collection),
      case_study: Boolean(item.case_study),
      production: Boolean(item.production),
      qc: Boolean(item.qc),
      billing: Boolean(item.billing),
      transportation: Boolean(item.transportation),
      payment_collection: Boolean(item.payment_collection),
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
      branch_type_name: form.branch_type_name.trim(),
      work_collection: Boolean(form.work_collection),
      case_study: Boolean(form.case_study),
      production: Boolean(form.production),
      qc: Boolean(form.qc),
      billing: Boolean(form.billing),
      transportation: Boolean(form.transportation),
      payment_collection: Boolean(form.payment_collection),
      status: form.status,
    }

    try {
      if (editingId) {
        await updateBranchType(editingId, payload)
        setMessage("Branch type updated successfully.")
      } else {
        await createBranchType(payload)
        setMessage("Branch type created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(branchTypeId, branchTypeName) {
    const confirmed = window.confirm(
      `Delete branch type "${branchTypeName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteBranchType(branchTypeId)
      if (editingId === branchTypeId) {
        resetForm()
      }
      setMessage("Branch type deleted successfully.")
      await load(search)
    } catch (err) {
      setError(err.message)
    }
  }

  function onSearchSubmit(event) {
    event.preventDefault()
    load(search)
  }

  const colSpan = FLAG_FIELDS.length + 3

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Branch Type Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete branch types.
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
          {editingId ? "Edit Branch Type" : "Create Branch Type"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm md:col-span-2">
            <span className="mb-1 block font-medium text-slate-700">Branch Type</span>
            <input
              type="text"
              required
              maxLength={100}
              value={form.branch_type_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, branch_type_name: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. Head Office"
            />
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

          <fieldset className="md:col-span-3">
            <legend className="mb-2 text-sm font-medium text-slate-700">
              Functions
            </legend>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {FLAG_FIELDS.map((field) => (
                <label
                  key={field.key}
                  className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700"
                >
                  <input
                    type="checkbox"
                    checked={Boolean(form[field.key])}
                    onChange={(e) =>
                      setForm((prev) => ({ ...prev, [field.key]: e.target.checked }))
                    }
                    className="h-4 w-4 rounded border-slate-300"
                  />
                  {field.label}
                </label>
              ))}
            </div>
          </fieldset>

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
          <h2 className="text-lg font-medium text-slate-800">Branch Type List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Branch Type"
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
                  Branch Type
                </th>
                {FLAG_FIELDS.map((field) => (
                  <th
                    key={field.key}
                    className="px-3 py-2 text-left font-semibold text-slate-700"
                  >
                    {field.label}
                  </th>
                ))}
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Status</th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={colSpan} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={colSpan} className="px-3 py-6 text-center text-slate-500">
                    No branch types found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.branch_type_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.branch_type_name}</td>
                    {FLAG_FIELDS.map((field) => (
                      <td key={field.key} className="px-3 py-2 text-slate-700">
                        {item[field.key] ? "Yes" : "No"}
                      </td>
                    ))}
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
                          onDelete(item.branch_type_id, item.branch_type_name)
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
