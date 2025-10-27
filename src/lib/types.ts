export interface UserResponse {
  id: number;
  username: string;
  email?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Book {
  id: number;
  title: string;
  author?: string | null;
  cover_image_url?: string | null;
  review_text?: string | null;
  is_recommended?: boolean | null;
  read_on?: string;
  created_at?: string;
}

export interface BookCreate {
  title: string;
  author?: string | null;
  review_text?: string | null;
  is_recommended?: boolean | null;
  read_on?: string | null;
}

export type BookUpdate = Partial<BookCreate>;
