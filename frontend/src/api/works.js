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

export function listWorks(search = "", sectionId = "") {
  const params = new URLSearchParams()
  if (search) params.set("search", search)
  if (sectionId) params.set("section_id", String(sectionId))
  const query = params.toString() ? `?${params.toString()}` : ""
  return request(`/works${query}`)
}

export function createWork(payload) {
  return request("/works", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function updateWork(workId, payload) {
  return request(`/works/${encodeURIComponent(workId)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export function deleteWork(workId) {
  return request(`/works/${encodeURIComponent(workId)}`, {
    method: "DELETE",
  })
}
