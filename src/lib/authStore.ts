import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { UserResponse } from '$lib/types';

// define the interface for the global Auth state
interface AuthState {
    isAuthenticated: boolean;
    user: UserResponse | null;
    token: string | null;
}

// helper to safely load data from localStorage
const getInitialState = (): AuthState => {
    if (browser) {
        // attempt to load  token & user data from storage
        const storedToken = localStorage.getItem('accessToken');
        const storedUser = localStorage.getItem('currentUser');

        if (storedToken && storedUser) {
            try {
                return {
                    isAuthenticated: true,
                    user: JSON.parse(storedUser) as UserResponse,
                    token: storedToken
                };
            } catch (e) {
                // clear storage if parsing fails
                localStorage.clear();
            }
        }
    }
    return { isAuthenticated: false, user: null, token: null}
};

// create the writable store w/ the initial state
export const authStore = writable<AuthState>(getInitialState());

// actions (fncts to modify the store)

// 1. log the user in (called after succesful login POST)
export const login = (token: string, user: UserResponse) => {
    authStore.set({
        isAuthenticated: true,
        user: user,
        token: token
    });

    // persist data for session management (safe only in browser)
    if (browser) {
        localStorage.setItem('accessToken', token);
        localStorage.setItem('currentUser', JSON.stringify(user));
    }
};

// 2. log the user out (when clicks 'logout')
export const logout = () => {
    authStore.set({
        isAuthenticated: false,
        user: null,
        token: null
    });

    // clear persisted data
    if (browser) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('currentUser');
    }
}