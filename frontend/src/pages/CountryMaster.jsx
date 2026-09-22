import { useEffect, useState } from "react"
import {
  createCountry,
  deleteCountry,
  listCountries,
  updateCountry,
} from "../api/countries"
import { listCurrencies } from "../api/currencies"

const emptyForm = {
  country_name: "",
  country_code: "",
  currency_id: "",
  status: "Active",
}

export default function CountryMaster() {
  const [items, setItems] = useState([])
  const [currencies, setCurrencies] = useState([])
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
      const data = await listCountries(searchTerm)
      setItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadCurrencies() {
    try {
      const data = await listCurrencies("")
      setCurrencies(data.filter((item) => item.status === "Active"))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load("")
    loadCurrencies()
  }, [])

  function resetForm() {
    setForm(emptyForm)
    setEditingId(null)
  }

  function onEdit(item) {
    setEditingId(item.country_id)
    setForm({
      country_name: item.country_name,
      country_code: item.country_code,
      currency_id: String(item.currency_id),
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
      country_name: form.country_name.trim(),
      country_code: form.country_code.trim().toUpperCase(),
      currency_id: Number(form.currency_id),
      status: form.status,
    }

    try {
      if (editingId) {
        await updateCountry(editingId, payload)
        setMessage("Country updated successfully.")
      } else {
        await createCountry(payload)
        setMessage("Country created successfully.")
      }
      resetForm()
      await load(search)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(countryId, countryName) {
    const confirmed = window.confirm(
      `Delete country "${countryName}"? This cannot be undone.`,
    )
    if (!confirmed) return

    setError("")
    setMessage("")
    try {
      await deleteCountry(countryId)
      if (editingId === countryId) {
        resetForm()
      }
      setMessage("Country deleted successfully.")
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
        <h1 className="text-2xl font-semibold text-slate-900">Country Master</h1>
        <p className="text-sm text-slate-600">
          Create, search, edit, and delete countries.
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
          {editingId ? "Edit Country" : "Create Country"}
        </h2>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Country Name</span>
            <input
              type="text"
              required
              maxLength={100}
              value={form.country_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, country_name: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. United States"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Country Code</span>
            <input
              type="text"
              required
              maxLength={10}
              value={form.country_code}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  country_code: e.target.value.toUpperCase(),
                }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              placeholder="e.g. US"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Currency</span>
            <select
              required
              value={form.currency_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, currency_id: e.target.value }))
              }
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
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

          <div className="md:col-span-2 flex gap-2">
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
          <h2 className="text-lg font-medium text-slate-800">Country List</h2>
          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, code, or currency"
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
                  Country Name
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Country Code
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Currency
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
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                    No countries found.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.country_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700">{item.country_name}</td>
                    <td className="px-3 py-2 font-medium text-slate-900">
                      {item.country_code}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {item.currency_name || "-"}
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
                        onClick={() => onDelete(item.country_id, item.country_name)}
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
