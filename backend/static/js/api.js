const api = {
    _parseError(text, statusText) {
        try {
            const json = JSON.parse(text);
            const detail = json.detail;
            if (typeof detail === "string") return detail;
            if (Array.isArray(detail)) return detail.map(e => e.msg || JSON.stringify(e)).join("; ");
            return json.message || text;
        } catch {
            return text || statusText;
        }
    },

    async get(path) {
        const resp = await fetch(`/api${path}`);
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(this._parseError(text, resp.statusText));
        }
        if (resp.status === 204) return null;
        return resp.json();
    },

    async post(path, body) {
        const resp = await fetch(`/api${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(this._parseError(text, resp.statusText));
        }
        return resp.json();
    },

    async put(path, body) {
        const resp = await fetch(`/api${path}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(this._parseError(text, resp.statusText));
        }
        return resp.json();
    },

    async del(path) {
        const resp = await fetch(`/api${path}`, { method: "DELETE" });
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(this._parseError(text, resp.statusText));
        }
        return null;
    },
};
