"use client";

import { useState } from "react";
import { motion } from "framer-motion";

export default function Home() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(""); // Process status
  const [automation, setAutomation] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState("");

  const startGeneration = async (prompt) => {
    setIsGenerating(true);
    setProgress(0);
    setStatus("🔄 Initializing video generation...");

    // If the prompt is blank, send an empty string (so backend auto-selects trending topic)
    const finalPrompt = prompt.trim() === "" ? "" : prompt;

    try {
      // Use relative URL (ensure your proxy is set in package.json or your API route forwards correctly)
      const response = await fetch("/api/generate_video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: finalPrompt }),
      });

      const result = await response.json();
      console.log("Backend Response:", result);

      if (result.success) {
        setStatus("🚀 Video generation started!");
        simulateProgress();
      } else {
        setStatus(`❌ Error: ${result.error || "Unknown error"}`);
        setIsGenerating(false);
      }
    } catch (error) {
      console.error("Error sending request to backend:", error);
      setStatus("❌ Error connecting to backend.");
      setIsGenerating(false);
    }
  };

  const simulateProgress = () => {
    let steps = [
      "⚡ Finding trending topic...",
      "🖼️ Generating images...",
      "🎬 Creating video...",
      "📦 Finalizing video...",
      "🚀 Uploading to YouTube...",
      "✅ Upload Successful!"
    ];

    let stepIndex = 0;
    let interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          return 100;
        }
        setStatus(steps[stepIndex] || "Processing...");
        stepIndex++;
        return prev + 20;
      });
    }, 1200);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white p-8">
      <motion.h1
        className="text-6xl font-extrabold mb-10 text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-yellow-500"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        ⚡ AI Video Generator
      </motion.h1>

      {/* Input Box */}
      <motion.input
        type="text"
        placeholder="🔍 Enter a topic (Leave blank for auto)"
        className="px-6 py-4 rounded-full text-black w-full max-w-lg shadow-lg focus:ring-4 focus:ring-red-400 text-lg"
        value={selectedTopic}
        onChange={(e) => setSelectedTopic(e.target.value)}
        whileFocus={{ scale: 1.05 }}
      />

      {/* Generate Button */}
      <motion.button
        className="mt-8 px-8 py-4 bg-gradient-to-r from-red-500 to-yellow-500 rounded-full shadow-xl hover:from-red-600 hover:to-yellow-600 text-white font-bold text-lg"
        onClick={() => startGeneration(selectedTopic)}
        whileHover={{ scale: 1.15, boxShadow: "0px 0px 20px rgba(255, 200, 50, 0.8)" }}
        whileTap={{ scale: 0.95 }}
      >
        🚀 Generate Video
      </motion.button>

      {/* Progress Bar & Status Updates */}
      {isGenerating && (
        <div className="mt-10 w-full max-w-lg">
          <p className="text-center mb-3 text-xl font-semibold">{status}</p>
          <motion.div
            className="h-4 rounded-full bg-gradient-to-r from-green-400 to-green-600 shadow-lg"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      )}

      {/* Automation Toggle */}
      <motion.div
        className="mt-10 px-8 py-3 rounded-full cursor-pointer shadow-lg text-lg font-bold"
        style={{ backgroundColor: automation ? "#00ff00" : "#444" }}
        onClick={() => setAutomation(!automation)}
        whileHover={{ scale: 1.1 }}
      >
        {automation ? "🔄 Automation: ON ✅" : "⚠️ Automation: OFF ❌"}
      </motion.div>

      {/* Floating UI Elements */}
      <motion.div
        className="fixed bottom-12 right-12 bg-red-600 text-white px-6 py-3 rounded-full shadow-lg text-lg"
        whileHover={{ scale: 1.15, rotate: 8 }}
        whileTap={{ scale: 0.9 }}
      >
        📂 Manage Videos
      </motion.div>
    </div>
  );
}
