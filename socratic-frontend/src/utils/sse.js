// Server-Sent Events parsing for the AI tutor stream.
//
// The backend emits events separated by a blank line ("\n\n"); each event
// carries an `event:` name line and a `data:` JSON line. This reads the body
// incrementally and invokes `onEvent(eventName, data)` for every complete event.

const parseRawEvent = (rawEvent, onEvent) => {
  let eventName = 'message';
  let dataStr = '';
  for (const line of rawEvent.split('\n')) {
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataStr += line.slice(5).trim();
    }
  }
  if (!dataStr) return;

  let data;
  try {
    data = JSON.parse(dataStr);
  } catch (e) {
    console.error('Failed to parse SSE data:', dataStr);
    return;
  }
  onEvent(eventName, data);
};

/**
 * Read an SSE Response body to completion, dispatching each event.
 * @param {Response} response - a streaming fetch Response (must have a body).
 * @param {(eventName: string, data: any) => void} onEvent
 */
export const consumeSSEStream = async (response, onEvent) => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      if (rawEvent.trim()) {
        parseRawEvent(rawEvent, onEvent);
      }
    }
  }

  // Flush any trailing event that lacked a final blank line.
  if (buffer.trim()) {
    parseRawEvent(buffer, onEvent);
  }
};
