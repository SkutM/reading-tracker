// src/lib/types.ts

export interface UserResponse {
  id: number;
  username: string;
  // add if your backend sends it:
  email?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Matches your FastAPI /books response (optional fields allowed)
export interface Book {
  id: number;
  title: string;
  author?: string | null;
  cover_image_url?: string | null;
  review_text?: string | null;
  is_recommended?: boolean | null;
  read_on?: string;     // ISO string from server
  created_at?: string;  // ISO string from server
}

// Request payload shapes
export interface BookCreate {
  title: string;
  author?: string | null;
  review_text?: string | null;
  is_recommended?: boolean | null;
  read_on?: string | null;
}

export type BookUpdate = Partial<BookCreate>;
