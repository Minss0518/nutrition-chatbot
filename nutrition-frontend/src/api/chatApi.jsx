const API_URL = "http://127.0.0.1:8000/chat";

export async function sendChatMessage(question) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) throw new Error("서버 오류");
  return await res.json();
}