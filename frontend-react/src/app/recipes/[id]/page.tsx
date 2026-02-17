import { RecipeDetailContent } from "./recipe-detail-content";

interface RecipeDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function RecipeDetailPage({ params }: RecipeDetailPageProps) {
  const { id } = await params;

  return <RecipeDetailContent id={id} />;
}
