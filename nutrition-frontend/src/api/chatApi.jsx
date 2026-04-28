// 배포 환경에서는 같은 서버에서 서빙되므로
const API_URL = "/chat";
const STREAM_URL = "/chat/stream";

// 기존 일반 요청 (그대로 유지)
export async function sendChatMessage(question, history = []) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });

  if (!res.ok) throw new Error("서버 오류");
  return await res.json();
}

// ✅ 스트리밍 + 히스토리 요청
export async function sendChatMessageStream(question, history = [], { onToken, onSources, onDone, onError }) {
  const res = await fetch(STREAM_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),  // ✅ 히스토리 포함
  });

  if (!res.ok) throw new Error("서버 오류");

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop();

    for (const part of parts) {
      const line = part.replace(/^data: /, "").trim();
      if (!line) continue;

      try {
        const parsed = JSON.parse(line);
        if (parsed.type === "token") onToken(parsed.content);
        else if (parsed.type === "sources") onSources(parsed.content);
        else if (parsed.type === "done") onDone();
        else if (parsed.type === "error") onError(parsed.content);
      } catch {
        // JSON 파싱 실패 무시
      }
    }
  }
}
