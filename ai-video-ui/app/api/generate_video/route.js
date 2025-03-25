import { NextResponse } from "next/server";

export async function POST(req) {
  try {
    const { prompt } = await req.json();

    // Use environment variable for backend URL, default to localhost:5000
    const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:5000";

    // Send the prompt to the Flask backend endpoint
    const response = await fetch(`${backendUrl}/generate_video`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      return new NextResponse(
        JSON.stringify({ success: false, error: data.error || "Unknown error" }),
        { status: 500 }
      );
    }

    return new NextResponse(
      JSON.stringify({ success: true, videoId: data.video_id }),
      { status: 200 }
    );
  } catch (error) {
    return new NextResponse(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500 }
    );
  }
}
