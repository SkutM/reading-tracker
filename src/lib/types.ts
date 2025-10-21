// auth above, prev below.

export interface UserResponse {
    id: number;
    username: string;
}

export interface Token {
    access_token: string;
    token_type: string;
    expires_in: number;
}

// below was here

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