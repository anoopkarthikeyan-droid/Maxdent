import { useEffect, useState } from "react"
import {
  approveSchedulerCase,
  deleteSchedulerCaseFile,
  getSchedulerCase,
  saveSchedulerCase,
  unapproveSchedulerCase,
  uploadSchedulerCaseFiles,
} from "../api/schedulers"

const TABS = [
  { id: "patient", label: "Patient" },
  { id: "images", label: "Images & Video" },
  { id: "plan", label: "Plan" },
  { id: "findings", label: "Findings" },
  { id: "history", label: "History" },
]

const FILE_GROUPS = [
  { kind: "extra_oral", label: "Extra Oral Image", accept: "image/*", video: false },
  { kind: "intra_oral", label: "Intra Oral Image", accept: "image/*", video: false },
  { kind: "ceph", label: "CEPH", accept: "image/*", video: false },
  { kind: "opg", label: "OPG", accept: "image/*", video: false },
  { kind: "video", label: "Video", accept: "video/*", video: true },
]

function emptyFiles() {
  return {
    extra_oral: [],
    intra_oral: [],
    ceph: [],
    opg: [],
    video: [],
    concern_video: [],
  }
}

function toForm(data) {
  return {
    working_doctor_name: data.working_doctor_name || "",
    clinic_name: data.clinic_name || "",
    mobile_no: data.mobile_no || "",
    email_id: data.email_id || "",
    patient_name: data.patient_name || "",
    age: data.age || "",
    sex: data.sex || "",
    patient_availability: data.patient_availability || "",
    next_appointment_date: data.next_appointment_date
      ? String(data.next_appointment_date).slice(0, 10)
      : "",
    stl_model_quality: data.stl_model_quality || "",
    chief_complaint: data.chief_complaint || "",
    other_concerns: data.other_concerns || "",
    type_of_plan: data.type_of_plan || "",
    type_of_case_study: data.type_of_case_study || "",
    suggestions_from_doctor: data.suggestions_from_doctor || "",
    deciduous_tooth: data.deciduous_tooth || "",
    rotation: data.rotation || "",
    molar_relation: data.molar_relation || "",
    overjet: data.overjet || "",
    overbite: data.overbite || "",
    missing_teeth: data.missing_teeth || "",
    midline_shift: data.midline_shift || "",
    crossbite: data.crossbite || "",
    arch_shape: data.arch_shape || "",
    deepbite: data.deepbite || "",
    open_bite: data.open_bite || "",
    spacing: data.spacing || "",
    caries_decay_root_stump: data.caries_decay_root_stump || "",
    impaction: data.impaction || "",
    periodontal_status: data.periodontal_status || "",
    extraction: data.extraction || "",
    rct: data.rct || "",
    crown_bridge_implant: data.crown_bridge_implant || "",
    tongue_thrusting: Boolean(data.tongue_thrusting),
    bruxism: data.bruxism || "",
    mouth_breathing: Boolean(data.mouth_breathing),
    thumb_sucking: Boolean(data.thumb_sucking),
    lip_biting: Boolean(data.lip_biting),
    medications: data.medications || "",
    allergies: data.allergies || "",
    remarks: data.remarks || "",
  }
}

function optional(value) {
  const cleaned = String(value || "").trim()
  return cleaned || null
}

function Field({ label, className = "", children }) {
  return (
    <label className={`block text-sm ${className}`}>
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      {children}
    </label>
  )
}

function CheckField({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 pb-2 text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-slate-300"
      />
      <span className="font-medium text-slate-700">{label}</span>
    </label>
  )
}

export default function SchedulerCasePanel({
  schedulerId,
  detailId,
  workNo,
  onClose,
  onSaved,
}) {
  const [tab, setTab] = useState("patient")
  const [form, setForm] = useState(toForm({}))
  const [files, setFiles] = useState(emptyFiles())
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [approving, setApproving] = useState(false)
  const [uploading, setUploading] = useState("")
  const [exists, setExists] = useState(false)
  const [approvalStatus, setApprovalStatus] = useState("Pending")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const locked = approvalStatus === "Approved"

  const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"

  function patch(partial) {
    setForm((prev) => ({ ...prev, ...partial }))
  }

  async function loadCase() {
    setLoading(true)
    setError("")
    try {
      const data = await getSchedulerCase(schedulerId, detailId)
      setForm(toForm(data))
      setFiles({ ...emptyFiles(), ...(data.files || {}) })
      setExists(Boolean(data.exists))
      setApprovalStatus(data.approval_status || "Pending")
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCase()
  }, [schedulerId, detailId])

  async function onSave(event) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")
    const payload = {
      ...form,
      working_doctor_name: optional(form.working_doctor_name),
      clinic_name: optional(form.clinic_name),
      mobile_no: optional(form.mobile_no),
      email_id: optional(form.email_id),
      patient_name: optional(form.patient_name),
      age: optional(form.age),
      sex: form.sex || null,
      patient_availability: optional(form.patient_availability),
      next_appointment_date: form.next_appointment_date || null,
      stl_model_quality: form.stl_model_quality || null,
      chief_complaint: optional(form.chief_complaint),
      other_concerns: optional(form.other_concerns),
      type_of_plan: form.type_of_plan || null,
      type_of_case_study: form.type_of_case_study || null,
      suggestions_from_doctor: optional(form.suggestions_from_doctor),
      deciduous_tooth: optional(form.deciduous_tooth),
      rotation: optional(form.rotation),
      molar_relation: optional(form.molar_relation),
      overjet: optional(form.overjet),
      overbite: optional(form.overbite),
      missing_teeth: optional(form.missing_teeth),
      midline_shift: optional(form.midline_shift),
      crossbite: optional(form.crossbite),
      arch_shape: optional(form.arch_shape),
      deepbite: optional(form.deepbite),
      open_bite: optional(form.open_bite),
      spacing: optional(form.spacing),
      caries_decay_root_stump: optional(form.caries_decay_root_stump),
      impaction: optional(form.impaction),
      periodontal_status: optional(form.periodontal_status),
      extraction: optional(form.extraction),
      rct: optional(form.rct),
      crown_bridge_implant: optional(form.crown_bridge_implant),
      bruxism: optional(form.bruxism),
      medications: optional(form.medications),
      allergies: form.allergies || null,
      remarks: optional(form.remarks),
      tongue_thrusting: Boolean(form.tongue_thrusting),
      mouth_breathing: Boolean(form.mouth_breathing),
      thumb_sucking: Boolean(form.thumb_sucking),
      lip_biting: Boolean(form.lip_biting),
    }
    try {
      const data = await saveSchedulerCase(schedulerId, detailId, payload)
      setForm(toForm(data))
      setFiles({ ...emptyFiles(), ...(data.files || {}) })
      setExists(true)
      setApprovalStatus(data.approval_status || "Pending")
      setMessage(exists ? "Case study updated successfully." : "Case study saved successfully.")
      onSaved?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function applyCase(data, successMessage) {
    setForm(toForm(data))
    setFiles({ ...emptyFiles(), ...(data.files || {}) })
    setExists(Boolean(data.exists))
    setApprovalStatus(data.approval_status || "Pending")
    setMessage(successMessage)
    onSaved?.()
  }

  async function onApprove() {
    setApproving(true)
    setError("")
    setMessage("")
    try {
      const data = await approveSchedulerCase(schedulerId, detailId)
      await applyCase(data, "Case study approved.")
    } catch (err) {
      setError(err.message)
    } finally {
      setApproving(false)
    }
  }

  async function onUnlock() {
    setApproving(true)
    setError("")
    setMessage("")
    try {
      const data = await unapproveSchedulerCase(schedulerId, detailId)
      await applyCase(data, "Case study unlocked for update.")
    } catch (err) {
      setError(err.message)
    } finally {
      setApproving(false)
    }
  }

  async function onUpload(kind, fileList) {
    if (!fileList?.length) return
    setUploading(kind)
    setError("")
    try {
      const uploaded = await uploadSchedulerCaseFiles(
        schedulerId,
        detailId,
        kind,
        fileList,
      )
      setFiles((prev) => ({
        ...prev,
        [kind]: [...(prev[kind] || []), ...uploaded],
      }))
      setMessage("Files uploaded successfully.")
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading("")
    }
  }

  async function onDeleteFile(kind, fileId) {
    setError("")
    try {
      await deleteSchedulerCaseFile(schedulerId, detailId, fileId)
      setFiles((prev) => ({
        ...prev,
        [kind]: (prev[kind] || []).filter((item) => item.file_id !== fileId),
      }))
    } catch (err) {
      setError(err.message)
    }
  }

  function FileBlock({ kind, label, accept, video }) {
    const items = files[kind] || []
    return (
      <div className="rounded-md border border-slate-200 p-3">
        <div className="mb-2 flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-slate-800">{label}</h3>
          <label className="cursor-pointer rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50">
            {uploading === kind ? "Uploading..." : "Add files"}
            <input
              type="file"
              multiple
              accept={accept}
              className="hidden"
              disabled={locked || Boolean(uploading)}
              onChange={(e) => {
                onUpload(kind, e.target.files)
                e.target.value = ""
              }}
            />
          </label>
        </div>
        {items.length === 0 ? (
          <p className="text-xs text-slate-500">No files uploaded.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <div key={item.file_id} className="rounded-md border border-slate-200 p-2">
                {video ? (
                  <video
                    controls
                    src={item.file_path}
                    className="h-32 w-full rounded bg-black object-contain"
                  />
                ) : (
                  <img
                    src={item.file_path}
                    alt={item.original_name || label}
                    className="h-32 w-full rounded object-cover"
                  />
                )}
                <div className="mt-2 flex items-center justify-between gap-2">
                  <span className="truncate text-xs text-slate-600">
                    {item.original_name || "File"}
                  </span>
                  <button
                    type="button"
                    disabled={locked}
                    onClick={() => onDeleteFile(kind, item.file_id)}
                    className="rounded border border-red-200 px-2 py-0.5 text-xs text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-medium text-slate-800">Case Study</h2>
          <p className="text-xs text-slate-500">
            Work {workNo}
            {exists ? ` · ${approvalStatus}` : " · Draft"}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Close
        </button>
      </div>

      {(error || message) && (
        <div
          className={`mb-4 rounded-md px-4 py-3 text-sm ${
            error
              ? "border border-red-200 bg-red-50 text-red-700"
              : "border border-emerald-200 bg-emerald-50 text-emerald-700"
          }`}
        >
          {error || message}
        </div>
      )}

      <div className="mb-4 flex flex-wrap gap-2">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              tab === item.id
                ? "bg-slate-900 text-white"
                : "border border-slate-300 text-slate-700 hover:bg-slate-50"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading case study...</p>
      ) : (
        <form onSubmit={onSave} className="space-y-4">
          <fieldset disabled={locked} className="space-y-4">
          {tab === "patient" && (
            <div className="grid gap-4 md:grid-cols-3">
              <Field label="Working Doctors Name" className="md:col-span-2">
                <input
                  type="text"
                  maxLength={150}
                  value={form.working_doctor_name}
                  onChange={(e) => patch({ working_doctor_name: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Clinic Name">
                <input
                  type="text"
                  maxLength={150}
                  value={form.clinic_name}
                  onChange={(e) => patch({ clinic_name: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Mobile No">
                <input
                  type="text"
                  maxLength={30}
                  value={form.mobile_no}
                  onChange={(e) => patch({ mobile_no: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Email Id">
                <input
                  type="email"
                  maxLength={150}
                  value={form.email_id}
                  onChange={(e) => patch({ email_id: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Patient Name">
                <input
                  type="text"
                  maxLength={150}
                  value={form.patient_name}
                  onChange={(e) => patch({ patient_name: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Age">
                <input
                  type="text"
                  maxLength={20}
                  value={form.age}
                  onChange={(e) => patch({ age: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Sex">
                <select
                  value={form.sex}
                  onChange={(e) => patch({ sex: e.target.value })}
                  className={inputClass}
                >
                  <option value="">Select</option>
                  <option value="M">M</option>
                  <option value="F">F</option>
                </select>
              </Field>
              <Field label="Patient Availability">
                <input
                  type="text"
                  maxLength={255}
                  value={form.patient_availability}
                  onChange={(e) => patch({ patient_availability: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Next Appointment Date">
                <input
                  type="date"
                  value={form.next_appointment_date}
                  onChange={(e) => patch({ next_appointment_date: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="STL / Model Quality">
                <select
                  value={form.stl_model_quality}
                  onChange={(e) => patch({ stl_model_quality: e.target.value })}
                  className={inputClass}
                >
                  <option value="">Select</option>
                  <option value="Good">Good</option>
                  <option value="Bad">Bad</option>
                </select>
              </Field>
            </div>
          )}

          {tab === "images" && (
            <div className="space-y-4">
              {FILE_GROUPS.map((group) => (
                <FileBlock key={group.kind} {...group} />
              ))}
            </div>
          )}

          {tab === "plan" && (
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Chief Complaint" className="md:col-span-2">
                <textarea
                  rows={3}
                  maxLength={1000}
                  value={form.chief_complaint}
                  onChange={(e) => patch({ chief_complaint: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label="Other Concerns" className="md:col-span-2">
                <textarea
                  rows={3}
                  maxLength={1000}
                  value={form.other_concerns}
                  onChange={(e) => patch({ other_concerns: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <div className="md:col-span-2">
                <FileBlock
                  kind="concern_video"
                  label="Video"
                  accept="video/*"
                  video
                />
              </div>
              <Field label="Type Of Plan">
                <select
                  value={form.type_of_plan}
                  onChange={(e) => patch({ type_of_plan: e.target.value })}
                  className={inputClass}
                >
                  <option value="">Select</option>
                  <option value="BOTH ARCH">BOTH ARCH</option>
                  <option value="UPPER ARCH ONLY">UPPER ARCH ONLY</option>
                  <option value="LOWER ARCH ONLY">LOWER ARCH ONLY</option>
                </select>
              </Field>
              <Field label="Type Of Case Study">
                <select
                  value={form.type_of_case_study}
                  onChange={(e) => patch({ type_of_case_study: e.target.value })}
                  className={inputClass}
                >
                  <option value="">Select</option>
                  <option value="CASUAL REPORT">CASUAL REPORT</option>
                  <option value="VIDEO REPORT">VIDEO REPORT</option>
                </select>
              </Field>
              <Field label="Suggestions From Doctor" className="md:col-span-2">
                <textarea
                  rows={3}
                  maxLength={1000}
                  value={form.suggestions_from_doctor}
                  onChange={(e) => patch({ suggestions_from_doctor: e.target.value })}
                  className={inputClass}
                />
              </Field>
            </div>
          )}

          {tab === "findings" && (
            <div className="space-y-5">
              <div>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-700">
                  Dental Findings
                </h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <Field label="Deciduous Tooth">
                    <input
                      type="text"
                      value={form.deciduous_tooth}
                      onChange={(e) => patch({ deciduous_tooth: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Rotation">
                    <input
                      type="text"
                      value={form.rotation}
                      onChange={(e) => patch({ rotation: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Molar Relation">
                    <input
                      type="text"
                      value={form.molar_relation}
                      onChange={(e) => patch({ molar_relation: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Overjet">
                    <input
                      type="text"
                      value={form.overjet}
                      onChange={(e) => patch({ overjet: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Overbite">
                    <input
                      type="text"
                      value={form.overbite}
                      onChange={(e) => patch({ overbite: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Missing Teeth">
                    <input
                      type="text"
                      value={form.missing_teeth}
                      onChange={(e) => patch({ missing_teeth: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Midline Shift">
                    <input
                      type="text"
                      value={form.midline_shift}
                      onChange={(e) => patch({ midline_shift: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Crossbite">
                    <input
                      type="text"
                      value={form.crossbite}
                      onChange={(e) => patch({ crossbite: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Arch Shape">
                    <input
                      type="text"
                      value={form.arch_shape}
                      onChange={(e) => patch({ arch_shape: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Deepbite">
                    <input
                      type="text"
                      value={form.deepbite}
                      onChange={(e) => patch({ deepbite: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Open Bite">
                    <input
                      type="text"
                      value={form.open_bite}
                      onChange={(e) => patch({ open_bite: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Spacing">
                    <input
                      type="text"
                      value={form.spacing}
                      onChange={(e) => patch({ spacing: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Caries / Grossly Decayed / Root Stump" className="md:col-span-3">
                    <input
                      type="text"
                      value={form.caries_decay_root_stump}
                      onChange={(e) =>
                        patch({ caries_decay_root_stump: e.target.value })
                      }
                      className={inputClass}
                    />
                  </Field>
                </div>
              </div>
              <div>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-700">
                  Radiographic Findings
                </h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Impaction">
                    <input
                      type="text"
                      value={form.impaction}
                      onChange={(e) => patch({ impaction: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Periodontal Status">
                    <input
                      type="text"
                      value={form.periodontal_status}
                      onChange={(e) => patch({ periodontal_status: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                </div>
              </div>
            </div>
          )}

          {tab === "history" && (
            <div className="space-y-5">
              <div>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-700">
                  Dental History
                </h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <Field label="Extraction">
                    <input
                      type="text"
                      value={form.extraction}
                      onChange={(e) => patch({ extraction: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="RCT">
                    <input
                      type="text"
                      value={form.rct}
                      onChange={(e) => patch({ rct: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Crown / Bridge / Implant">
                    <input
                      type="text"
                      value={form.crown_bridge_implant}
                      onChange={(e) =>
                        patch({ crown_bridge_implant: e.target.value })
                      }
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Bruxism">
                    <input
                      type="text"
                      value={form.bruxism}
                      onChange={(e) => patch({ bruxism: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <CheckField
                    label="Tongue Thrusting"
                    checked={form.tongue_thrusting}
                    onChange={(checked) => patch({ tongue_thrusting: checked })}
                  />
                  <CheckField
                    label="Mouth Breathing"
                    checked={form.mouth_breathing}
                    onChange={(checked) => patch({ mouth_breathing: checked })}
                  />
                  <CheckField
                    label="Thumb Sucking"
                    checked={form.thumb_sucking}
                    onChange={(checked) => patch({ thumb_sucking: checked })}
                  />
                  <CheckField
                    label="Lip Biting"
                    checked={form.lip_biting}
                    onChange={(checked) => patch({ lip_biting: checked })}
                  />
                </div>
              </div>
              <div>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-700">
                  Medical History
                </h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Medications" className="md:col-span-2">
                    <textarea
                      rows={5}
                      value={form.medications}
                      onChange={(e) => patch({ medications: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Allergies">
                    <select
                      value={form.allergies}
                      onChange={(e) => patch({ allergies: e.target.value })}
                      className={inputClass}
                    >
                      <option value="">Select</option>
                      <option value="PLASTIC">PLASTIC</option>
                      <option value="METAL">METAL</option>
                      <option value="LATEX">LATEX</option>
                      <option value="FOOD">FOOD</option>
                      <option value="MEDICATION">MEDICATION</option>
                    </select>
                  </Field>
                  <Field label="Remarks">
                    <input
                      type="text"
                      maxLength={1000}
                      value={form.remarks}
                      onChange={(e) => patch({ remarks: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                </div>
              </div>
            </div>
          )}

          </fieldset>

          <div className="flex flex-wrap gap-2 pt-2">
            {!locked && (
              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
              >
                {saving
                  ? exists
                    ? "Updating..."
                    : "Saving..."
                  : exists
                    ? "Update"
                    : "Save"}
              </button>
            )}
            {exists && !locked && (
              <button
                type="button"
                disabled={approving}
                onClick={onApprove}
                className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-60"
              >
                {approving ? "Approving..." : "Approve"}
              </button>
            )}
            {locked && (
              <button
                type="button"
                disabled={approving}
                onClick={onUnlock}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {approving ? "Unlocking..." : "Unlock for Update"}
              </button>
            )}
          </div>
        </form>
      )}
    </section>
  )
}
