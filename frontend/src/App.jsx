import { useState } from "react"

function App() {
  const [file, setFile] = useState(null)
  const [percent, setPercent] = useState(0)
  const [loading, setLoading] = useState(false)
  const [videoUrl, setVideoUrl] = useState(null)
  const [tracks, setTracks] = useState([])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setVideoUrl(null)
    setTracks([])
    setPercent(0)

    // POST the file
    const form = new FormData()
    form.append("video", file)
    await fetch("http://localhost:8000/track", { method: "POST", body: form })

    const interval = setInterval(async () => {
      const res = await fetch("http://localhost:8000/track")
      const data = await res.json()

      if (data.percent !== undefined) setPercent(data.percent)

      if (data.status === "done") {
        clearInterval(interval)
        setVideoUrl(data.result.video_url)
        setTracks(data.result.tracks)
        setLoading(false)
      } else if (data.status === "error") {
        clearInterval(interval)
        alert("Processing error: " + data.message)
        setLoading(false)
      }
    }, 1500)
  }

  return (
    <div>
      <h1>Salamander Tracker</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button type="submit" disabled={loading || !file}>
          {loading ? "Processing..." : "Upload"}
        </button>
      </form>

      {loading && (
        <div>
          <p>Processing video... {percent}%</p>
          <progress value={percent} max={100} />
        </div>
      )}

      {videoUrl && <video src={videoUrl} controls width={640} />}

      {tracks.length > 0 && (
        <table border="1" cellPadding="8">
          <thead>
            <tr>
              <th>Track ID</th>
              <th>Label</th>
              <th>Time on Screen (s)</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((t) => (
              <tr key={t.track_id}>
                <td>{t.track_id}</td>
                <td>{t.label}</td>
                <td>{t.time_on_screen_s}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default App