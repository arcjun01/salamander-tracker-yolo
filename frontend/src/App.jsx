import { useState } from "react"

function App() {
  const [file, setFile] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const form = new FormData()
    form.append("video", file)
    const res = await fetch("http://localhost:8000/track", {
      method: "POST",
      body: form,
    })
    const data = await res.json()
    setVideoUrl(data.video_url)
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
        <button type="submit" disabled={!file}>Upload</button>
      </form>
      {videoUrl && (
        <video src={videoUrl} controls width={640} />
      )}
    </div>
  )
}

export default App