const API_URL = 'http://127.0.0.1:8000'

export const fetchFileApiData = async () => {
  const response = await fetch(`${API_URL}/file_api_results`)
  return response.json()
}

export const pollFileApiData = (callback, interval = 2000) => {
  const poll = setInterval(async () => {
    try {
      const data = await fetchFileApiData()
      callback(data)
    } catch (error) {
      console.error('Poll error:', error)
    }
  }, interval)
  
  return () => clearInterval(poll)
}
