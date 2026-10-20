export default defineEventHandler(() => {
  const tasks = { Alpha: 3, Beta: 5, Gamma: 8 }
  return {
    owner: { name: 'Ada' },
    cards: Object.entries(tasks).map(([title, count]) => ({ title, count })),
    count: state.count,
  }
})
