import { useEffect, useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { approveSchedulerCase, listSchedulers } from "../api/schedulers"
import SchedulerCasePanel from "./SchedulerCasePanel"

export default function CaseStudyMaster() {
  const navigate = useNavigate()
  const { schedulerId, detailId } = useParams()
  const [items, setItems] = useState([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function load(searchTerm = search) {
    setLoading(true)
    setError("")
    try {
      const data = await listSchedulers(searchTerm)
      const rows = []
      for (const header of data) {
        for (const detail of header.details || []) {
          rows.push({
            scheduler_id: header.scheduler_id,
            scheduler_detail_id: detail.scheduler_detail_id,
            mdo_code: header.mdo_code,
            customer_name: header.customer_name,
            work_no: detail.work_no,
            work_name: detail.work_name,
            patient_name: detail.patient_name,
            has_case: Boolean(detail.has_case),
            approval_status: detail.case_approval_status || null,
          })
        }
      }
      setItems(rows)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load("")
  }, [])

  const selected = useMemo(() => {
    if (!schedulerId || !detailId) return null
    return items.find(
      (row) =>
        String(row.scheduler_id) === String(schedulerId) &&
        String(row.scheduler_detail_id) === String(detailId),
    )
  }, [items, schedulerId, detailId])

  function onSearchSubmit(event) {
    event.preventDefault()
    load(search)
  }

  function openCase(row) {
    navigate(`/case-studies/${row.scheduler_id}/${row.scheduler_detail_id}`)
  }

  async function onApprove(row) {
    if (!window.confirm(`Approve case study for "${row.work_no}"?`)) return
    setError("")
    try {
      await approveSchedulerCase(row.scheduler_id, row.scheduler_detail_id)
      await load(search)
    } catch (err) {
      setError(err.message)
    }
  }

  function statusLabel(row) {
    if (row.approval_status === "Approved") return "Approved"
    if (row.has_case) return "Pending"
    return "Draft"
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Case Study</h1>
        <p className="mt-1 text-sm text-slate-500">
          Save or update a case study, then approve it. Approved records are
          locked until unlocked for further update.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {schedulerId && detailId ? (
        <SchedulerCasePanel
          schedulerId={Number(schedulerId)}
          detailId={Number(detailId)}
          workNo={selected?.work_no || ""}
          onClose={() => navigate("/case-studies")}
          onSaved={() => load(search)}
        />
      ) : null}

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-medium text-slate-800">Work List</h2>
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
                  Work No
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Customer
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Work Name
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Patient Name
                </th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">
                  Status
                </th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                    No scheduler work rows found. Save a scheduler first.
                  </td>
                </tr>
              ) : (
                items.map((row) => (
                  <tr key={row.scheduler_detail_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium text-slate-800">
                      {row.work_no}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{row.customer_name}</td>
                    <td className="px-3 py-2 text-slate-700">{row.work_name}</td>
                    <td className="px-3 py-2 text-slate-700">{row.patient_name}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {statusLabel(row)}
                    </td>
                    <td className="px-3 py-2 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => openCase(row)}
                        className="mr-2 rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-white"
                      >
                        {row.has_case ? "Update" : "Case Study"}
                      </button>
                      {row.has_case && row.approval_status !== "Approved" ? (
                        <button
                          type="button"
                          onClick={() => onApprove(row)}
                          className="rounded-md border border-emerald-300 px-2 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-50"
                        >
                          Approve
                        </button>
                      ) : null}
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
