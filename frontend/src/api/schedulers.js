const API_BASE = "/api"

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  })

  if (response.status === 204) {
    return null
  }

  let data = null
  const text = await response.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }

  if (!response.ok) {
    const detail = data?.detail
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || JSON.stringify(item)).join(", ")
          : "Request failed"
    throw new Error(message)
  }

  return data
}

export function listSchedulers(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : ""
  return request(`/schedulers${query}`)
}

export function getNextSchedulerCode(customerId, workReceivedDate) {
  const params = new URLSearchParams({
    customer_id: String(customerId),
    work_received_date: workReceivedDate,
  })
  return request(`/schedulers/next-code?${params.toString()}`)
}

export function createScheduler(payload) {
  return request("/schedulers", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function updateScheduler(schedulerId, payload) {
  return request(`/schedulers/${encodeURIComponent(schedulerId)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export function deleteScheduler(schedulerId) {
  return request(`/schedulers/${encodeURIComponent(schedulerId)}`, {
    method: "DELETE",
  })
}

export function getSchedulerCase(schedulerId, detailId) {
  return request(
    `/schedulers/${encodeURIComponent(schedulerId)}/details/${encodeURIComponent(detailId)}/case`,
  )
}

export function saveSchedulerCase(schedulerId, detailId, payload) {
  return request(
    `/schedulers/${encodeURIComponent(schedulerId)}/details/${encodeURIComponent(detailId)}/case`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  )
}

export function approveSchedulerCase(schedulerId, detailId) {
  return request(
    `/schedulers/${encodeURIComponent(schedulerId)}/details/${encodeURIComponent(detailId)}/case/approve`,
    { method: "POST" },
  )
}

export function unapproveSchedulerCase(schedulerId, detailId) {
  return request(
    `/schedulers/${encodeURIComponent(schedulerId)}/details/${encodeURIComponent(detailId)}/case/unapprove`,
    { method: "POST" },
  )
}

export async function uploadSchedulerCaseFiles(schedulerId, detailId, kind, files) {
  const formData = new FormData()
  for (const file of files) {
    formData.append("files", file)
  }
  const response = await fetch(
    `${API_BASE}/schedulers/${encodeURIComponent(schedulerId)}/details/${encodeURIComponent(detailId)}/case/files?kind=${encodeURIComponent(kind)}`,
    {
      method: "POST",
      body: formData,
    },
  )
  const text = await response.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }
  if (!response.ok) {
    const detail = data?.detail
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || JSON.stringify(item)).join(", ")
          : "Upload failed",
    )
  }
  return data
}

export function deleteSchedulerCaseFile(schedulerId, detailId, fileId) {
  return request(
    `/schedulers/${encodeURIComponent(schedulerId)}/details/${encodeURIComponent(detailId)}/case/files/${encodeURIComponent(fileId)}`,
    { method: "DELETE" },
  )
}
