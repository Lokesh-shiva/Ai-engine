"use client";
import { useState } from "react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [videoId, setVideoId] = useState(null);
  const [error, setError] = useState("");

  const generateVideo = async () => {
    setLoading(true);
    setVideoId(null);
    setError("");

    try {
      const response = await fetch("/api/generate_video", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error);
      }

      setVideoId(data.videoId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>AI Video Generator</h1>
      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter a prompt..."
      />
      <button onClick={generateVideo} disabled={loading}>
        {loading ? "Generating..." : "Generate Video"}
      </button>

      {videoId && (
        <p>
          ✅ Video Uploaded:{" "}
          <a href={`https://www.youtube.com/watch?v=${videoId}`} target="_blank">
            Watch Here
          </a>
        </p>
      )}

      {error && <p style={{ color: "red" }}>❌ {error}</p>}
    </div>
  );
}
