import { api } from "@/lib/api";
import type { User } from "@/types";

export interface UserProfileUpdate {
  name?: string;
}

export interface UserPasswordUpdate {
  current_password: string;
  new_password: string;
}

export interface UserProfileResponse extends User {
  credits_balance: number;
}

export const userService = {
  getProfile: async (): Promise<UserProfileResponse> => {
    const response = await api.get<UserProfileResponse>("/users/me");
    return response.data;
  },

  updateProfile: async (data: UserProfileUpdate): Promise<User> => {
    const response = await api.put<User>("/users/me", data);
    return response.data;
  },

  updatePassword: async (data: UserPasswordUpdate): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>("/users/me/password", data);
    return response.data;
  },
};
