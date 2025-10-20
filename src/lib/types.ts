export interface Book {
    id: number;
    title: string;
    author: string | null;
    cover_image_url: string | null;
    review_text: string | null;
    is_recommended: boolean | null;
    read_on: string;
    created_at: string;
}