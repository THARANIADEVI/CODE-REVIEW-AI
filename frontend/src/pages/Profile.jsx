import { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { updateProfile, resetPassword } from "../services/api";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [profileForm, setProfileForm] = useState({ name: user?.name || "", email: user?.email || "" });
  const [profileMsg, setProfileMsg] = useState("");
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "" });
  const [pwMsg, setPwMsg] = useState("");

  const saveProfile = async (e) => {
    e.preventDefault();
    setProfileMsg("");
    try {
      const res = await updateProfile(profileForm);
      updateUser(res.data.user);
      setProfileMsg("Profile updated.");
    } catch (err) {
      setProfileMsg(err.response?.data?.error || "Update failed");
    }
  };

  const savePassword = async (e) => {
    e.preventDefault();
    setPwMsg("");
    try {
      await resetPassword(pwForm);
      setPwMsg("Password updated.");
      setPwForm({ current_password: "", new_password: "" });
    } catch (err) {
      setPwMsg(err.response?.data?.error || "Reset failed");
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="card p-6">
        <h2 className="text-xl font-bold mb-4">Update Profile</h2>
        {profileMsg && <p className="text-sm mb-3 text-brand-600">{profileMsg}</p>}
        <form onSubmit={saveProfile} className="space-y-3">
          <input
            className="input"
            value={profileForm.name}
            onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
            placeholder="Name"
          />
          <input
            className="input"
            value={profileForm.email}
            onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
            placeholder="Email"
          />
          <button className="btn-primary">Save</button>
        </form>
      </div>

      <div className="card p-6">
        <h2 className="text-xl font-bold mb-4">Reset Password</h2>
        {pwMsg && <p className="text-sm mb-3 text-brand-600">{pwMsg}</p>}
        <form onSubmit={savePassword} className="space-y-3">
          <input
            type="password"
            className="input"
            placeholder="Current password"
            value={pwForm.current_password}
            onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })}
          />
          <input
            type="password"
            className="input"
            placeholder="New password"
            value={pwForm.new_password}
            onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
          />
          <button className="btn-primary">Update Password</button>
        </form>
      </div>
    </div>
  );
}
