import React, { useState } from 'react';
import './App.css';
import { fetchEventSource } from '@microsoft/fetch-event-source';

interface Message {
  message: string;
  isUser: boolean;
  sources?: string[];
}

function App() {
  const BACKEND_URL = "http://localhost:5433"
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);

  const setPartialMessage = (chunk: string, sources: string[] = []) => {
    setMessages(prevMessages => {
      let lastMessage = prevMessages[prevMessages.length - 1];
      if (prevMessages.length === 0 || !lastMessage.isUser) {
        return [
          ...prevMessages.slice(0, -1),
          {
            message: lastMessage.message + chunk,
            isUser: false,
            sources: lastMessage.sources
              ? [...lastMessage.sources, ...sources]
              : sources,
          },
        ];
      }

      return [...prevMessages, { message: chunk, isUser: false, sources }];
    });
  };

  const handleReceiveMessage = (data: string) => {
    const parsedData = JSON.parse(data);
    if (parsedData.answer) {
      setPartialMessage(parsedData.answer);
    }
    if (parsedData.docs) {
      setPartialMessage(
        '',
        parsedData.docs.map((doc: any) => doc.metadata.source)
      );
    }
  };

  const handleSendMessage = async (message: string) => {
    setInputValue('');
    setMessages(prev => [...prev, { message, isUser: true }]);

    await fetchEventSource(`${BACKEND_URL}/rag/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: { question: message } }),
      onmessage(event) {
        console.log(event)
        if (event.event === 'data') handleReceiveMessage(event.data);
      },
    });
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage(inputValue.trim());
    }
  };

  const formatSource = (source: string) => source.split('/').pop() || '';

  return (
    <div className="app-container">
      <header className="header">Ansh's financial advisor</header>

      <main className="main">
        <div className="chat-window">
          <div className="chat-box">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`message ${msg.isUser ? 'user' : 'bot'}`}
              >
                {msg.message}
                {!msg.isUser && Array.isArray(msg.sources) && msg.sources.length > 0 && (
                  <div className="sources">
                    <hr />
                    {msg.sources.map((src, i) => (
                      <div key={i}>
                        <a
                          href={`${BACKEND_URL}/rag/static/${encodeURI(formatSource(src))}`}
                          target="_blank"
                          rel="noreferrer"
                          download
                        >
                          {formatSource(src)}
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="input-area">
            <textarea
              className="input-box"
              placeholder="Enter your message here..."
              onKeyUp={handleKeyPress}
              onChange={e => setInputValue(e.target.value)}
              value={inputValue}
            />
            <button className="send-button" onClick={() => handleSendMessage(inputValue.trim())}>
              Send
            </button>
          </div>
        </div>
      </main>

      <footer className="footer">
        *This AI agent can make mistakes. Consider checking important information.
        <br />
        All training data derived from public records.
        <br />
        <br />
      </footer>
    </div>
  );
}

export default App;
