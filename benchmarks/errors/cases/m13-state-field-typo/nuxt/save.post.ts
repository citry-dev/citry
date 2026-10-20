export default defineEventHandler(async (event) => {
  const { amount } = await readBody<{ amount: number }>(event)
  state.cuont += amount
  return { count: state.count }
})
