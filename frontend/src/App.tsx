import './App.css'
import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="app">
      <header>
        <h1>🏠 HomeQuest</h1>
        <p>できた！を残す。</p>
      </header>
      
      <main>
        <section className="welcome">
          <h2>ようこそ！</h2>
          <p>家事がゲームに変わる。AIが毎回違うクエストを生成します。</p>
        </section>

        <section className="features">
          <h3>こんなことができます：</h3>
          <ul>
            <li>✅ グループを作成して家族を招待</li>
            <li>🎮 AIが生成するクエストをプレイ</li>
            <li>💰 ポイントを稼いで報酬と交換</li>
            <li>⭐ クエストクリアで「できた！」を記録</li>
          </ul>
        </section>

        <section className="test">
          <h3>テストカウント: {count}</h3>
          <button onClick={() => setCount(count + 1)}>
            カウントアップ
          </button>
        </section>
      </main>
    </div>
  )
}

export default App
