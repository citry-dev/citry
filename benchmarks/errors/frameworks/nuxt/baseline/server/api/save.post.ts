export default defineEventHandler(async (event) => {
  const { amount } = await readBody<{ amount: number }>(event)
  state.count += amount
  return { count: state.count }
})
