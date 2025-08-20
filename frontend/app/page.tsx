'use client';

import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [username, setUsername] = useState('');
  const [token, setToken] = useState('');
  const [kbId, setKbId] = useState('default');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  const handleLogin = async () => {
    try {
      const formData = new FormData();
      formData.append('username', username);
      const res = await axios.post('http://localhost:8000/api/v1/login', formData);
      setToken(res.data.access_token);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAsk = async () => {
    try {
      const res = await axios.post(
        'http://localhost:8000/api/v1/query',
        { kb_id: kbId, query: question },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnswer(res.data.answer || JSON.stringify(res.data));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <main className="p-6 max-w-xl mx-auto space-y-4">
      {!token ? (
        <div className="space-y-2">
          <input
            className="border p-2 w-full"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <button
            onClick={handleLogin}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            登录
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <input
            className="border p-2 w-full"
            placeholder="知识库 ID"
            value={kbId}
            onChange={(e) => setKbId(e.target.value)}
          />
          <textarea
            className="border p-2 w-full"
            placeholder="请输入问题"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            onClick={handleAsk}
            className="px-4 py-2 bg-green-500 text-white rounded"
          >
            提问
          </button>
          {answer && (
            <div className="mt-4 p-2 border bg-white whitespace-pre-wrap">
              {answer}
            </div>
          )}
        </div>
      )}
    </main>
  );
}

