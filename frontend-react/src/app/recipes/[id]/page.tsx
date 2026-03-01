import { RecipeDetailContent } from "./recipe-detail-content";

interface RecipeDetailPageProps {
  readonly params: Promise<{
    readonly id: string;
  }>;
}

export default async function RecipeDetailPage({ params }: RecipeDetailPageProps) {
  const { id } = await params;

  return <RecipeDetailContent id={id} />;
}
