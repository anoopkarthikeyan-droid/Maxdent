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

export function listPlaces(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : ""
  return request(`/places${query}`)
}

export function createPlace(payload) {
  return request("/places", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function updatePlace(placeId, payload) {
  return request(`/places/${encodeURIComponent(placeId)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export function deletePlace(placeId) {
  return request(`/places/${encodeURIComponent(placeId)}`, {
    method: "DELETE",
  })
}
