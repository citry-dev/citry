export default async function Project({ params }: PageProps<"/projects/[id]">) {
  const { id } = await params;
  return <h1>Project {id}</h1>;
}
