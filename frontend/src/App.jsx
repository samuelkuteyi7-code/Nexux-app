import { useState } from 'react'
import './App.css'

const API = '/api'

export default function App() {
  const [profile, setProfile] = useState(null)
  const [world, setWorld] = useState(null)
  const [situation, setSituation] = useState(null)
  const [log, setLog] = useState([])
  const [form, setForm] = useState({ name: '', goal: '', interests: '' })

  async function createProfileAndWorld(e) {
    e.preventDefault()
    const profileRes = await fetch(`${API}/profile/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: form.name,
        goal: form.goal,
        interests: form.interests.split(',').map((s) => s.trim()).filter(Boolean),
      }),
    })
    const newProfile = await profileRes.json()
    setProfile(newProfile)

    const worldRes = await fetch(`${API}/world/generate/${newProfile.id}`, { method: 'POST' })
    const newWorld = await worldRes.json()
    setWorld(newWorld)

    await fetchSituation(newWorld.id)
  }

  async function fetchSituation(worldId) {
    const res = await fetch(`${API}/world/${worldId}/situation`)
    setSituation(await res.json())
  }

  async function choose(optionKey) {
    const effects = situation.options[optionKey]
    const res = await fetch(`${API}/decision/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        world_id: world.id,
        situation: situation.situation,
        choice_key: optionKey,
        option_effects: effects,
      }),
    })
    const decision = await res.json()
    setLog((prev) => [...prev, decision])

    const worldRes = await fetch(`${API}/world/${world.id}`)
    setWorld(await worldRes.json())

    await fetchSituation(world.id)
  }

  if (!world) {
    return (
      <main className="container">
        <h1>NEXUS</h1>
        <p className="tagline">Explore. Decide. Learn. Evolve.</p>
        <form onSubmit={createProfileAndWorld}>
          <label>
            Name
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Goal
            <input
              required
              placeholder="e.g. become a software developer"
              value={form.goal}
              onChange={(e) => setForm({ ...form, goal: e.target.value })}
            />
          </label>
          <label>
            Interests (comma separated)
            <input value={form.interests} onChange={(e) => setForm({ ...form, interests: e.target.value })} />
          </label>
          <button type="submit">Enter your world</button>
        </form>
      </main>
    )
  }

  return (
    <main className="container">
      <h1>NEXUS</h1>
      <section className="state-panel">
        <h2>World State</h2>
        <p>Time step: {world.state.time_step}</p>
        <p>Money: {world.state.resources.money} | Energy: {world.state.resources.energy}</p>
        <p>Skills: {Object.entries(world.state.skills).map(([k, v]) => `${k}: ${v}`).join(', ') || 'none yet'}</p>
      </section>

      {situation && (
        <section className="situation-panel">
          <h2>Situation</h2>
          <p>{situation.situation}</p>
          <div className="options">
            {Object.keys(situation.options).map((key) => (
              <button key={key} onClick={() => choose(key)}>
                {key.replace('_', ' ')}
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="log-panel">
        <h2>History</h2>
        <ul>
          {log.map((d) => (
            <li key={d.id}>{d.consequence}</li>
          ))}
        </ul>
      </section>
    </main>
  )
}
