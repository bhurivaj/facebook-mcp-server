import requests
from typing import Any
from config import GRAPH_API_BASE_URL, PAGE_ID, PAGE_ACCESS_TOKEN


class FacebookAPI:
    # Generic Graph API request method
    def _request(self, method: str, endpoint: str, params: dict[str, Any], json: dict[str, Any] = None) -> dict[str, Any]:
        url = f"{GRAPH_API_BASE_URL}/{endpoint}"
        params["access_token"] = PAGE_ACCESS_TOKEN
        response = requests.request(method, url, params=params, json=json)
        return response.json()

    def post_message(self, message: str) -> dict[str, Any]:
        return self._request("POST", f"{PAGE_ID}/feed", {"message": message})

    def reply_to_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        return self._request("POST", f"{comment_id}/comments", {"message": message})

    def get_posts(self) -> dict[str, Any]:
        return self._request("GET", f"{PAGE_ID}/posts", {"fields": "id,message,created_time"})

    def get_comments(self, post_id: str) -> dict[str, Any]:
        return self._request("GET", f"{post_id}/comments", {"fields": "id,message,from,created_time"})

    def delete_post(self, post_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"{post_id}", {})

    def delete_comment(self, comment_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"{comment_id}", {})

    def hide_comment(self, comment_id: str) -> dict[str, Any]:
        """Hide a comment from the Page."""
        return self._request("POST", f"{comment_id}", {"is_hidden": True})

    def unhide_comment(self, comment_id: str) -> dict[str, Any]:
        """Unhide a previously hidden comment."""
        return self._request("POST", f"{comment_id}", {"is_hidden": False})

    def get_insights(self, post_id: str, metric: str, period: str = "lifetime", breakdown: str = None) -> dict[str, Any]:
        params = {"metric": metric, "period": period}
        if breakdown:
            params["breakdown"] = breakdown
        return self._request("GET", f"{post_id}/insights", params)

    def get_bulk_insights(self, post_id: str, metrics: list[str], period: str = "lifetime") -> dict[str, Any]:
        metric_str = ",".join(metrics)
        return self.get_insights(post_id, metric_str, period)

    @staticmethod
    def extract_breakdown_value(response: dict[str, Any], dimension_value: str) -> Any:
        """Best-effort extraction of one dimension's value from an Insights
        `breakdown` response (e.g. metric=post_media_view&breakdown=is_from_ads).

        Meta's docs don't publish a worked JSON example for Page/post
        breakdowns, so this tries the two shapes seen elsewhere in the Graph
        API: a `value` dict keyed by the dimension's string (the legacy
        breakdown shape, e.g. page_fans_country), and the newer
        `total_value.breakdowns[].results[]` shape. Returns None if neither
        matches, so callers can fall back to the raw response instead of
        reporting a wrong number.
        """
        for item in response.get("data", []):
            for v in item.get("values", []):
                value = v.get("value")
                if isinstance(value, dict) and dimension_value in value:
                    return value[dimension_value]
            total = item.get("total_value")
            if isinstance(total, dict):
                for bd in total.get("breakdowns", []):
                    for result in bd.get("results", []):
                        if dimension_value in result.get("dimension_values", []):
                            return result.get("value")
        return None

    def post_image_to_facebook(self, image_url: str, caption: str) -> dict[str, Any]:
        params = {
            "url": image_url,
            "caption": caption
        }
        return self._request("POST", f"{PAGE_ID}/photos", params)
    
    def send_dm_to_user(self, user_id: str, message: str) -> dict[str, Any]:
        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message},
            "messaging_type": "RESPONSE"
        }
        return self._request("POST", "me/messages", {}, json=payload)
    
    def update_post(self, post_id: str, new_message: str) -> dict[str, Any]:
        return self._request("POST", f"{post_id}", {"message": new_message})

    def schedule_post(self, message: str, publish_time: int) -> dict[str, Any]:
        params = {
            "message": message,
            "published": False,
            "scheduled_publish_time": publish_time,
        }
        return self._request("POST", f"{PAGE_ID}/feed", params)

    def get_page_fan_count(self) -> int:
        data = self._request("GET", f"{PAGE_ID}", {"fields": "fan_count"})
        return data.get("fan_count", 0)

    def get_post_share_count(self, post_id: str) -> int:
        data = self._request("GET", f"{post_id}", {"fields": "shares"})
        return data.get("shares", {}).get("count", 0)

    def get_comment_replies(self, comment_id: str) -> dict[str, Any]:
        return self._request("GET", f"{comment_id}/comments", {"fields": "id,message,from,created_time"})

    def get_post_permalink(self, post_id: str) -> dict[str, Any]:
        return self._request("GET", f"{post_id}", {"fields": "permalink_url"})

    def get_scheduled_posts(self) -> dict[str, Any]:
        return self._request("GET", f"{PAGE_ID}/scheduled_posts", {"fields": "id,message,scheduled_publish_time"})

    def get_page_info(self) -> dict[str, Any]:
        fields = "name,about,category,website,emails,phone,description,location"
        return self._request("GET", f"{PAGE_ID}", {"fields": fields})
