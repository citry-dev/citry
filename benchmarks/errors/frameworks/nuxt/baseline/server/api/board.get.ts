export default defineEventHandler(() => {
  const tasks = { Alpha: 3, Beta: 5, Gamma: 8 }
  return {
    owner: { name: 'Ada' },
    // The heading's color, which the page's stylesheet reads.
    accent: 'rgb(0, 0, 255)',
    // The page draws a featured project's card with the accent border.
    cards: Object.entries(tasks).map(([title, count]) => ({ title, count, featured: title === 'Alpha' })),
    count: state.count,
  }
})
