from typing import Any
from facebook_api import FacebookAPI


class Manager:
    def __init__(self):
        self.api = FacebookAPI()

    def post_to_facebook(self, message: str) -> dict[str, Any]:
        return self.api.post_message(message)

    def reply_to_comment(self, post_id: str, comment_id: str, message: str) -> dict[str, Any]:
        return self.api.reply_to_comment(comment_id, message)

    def get_page_posts(self) -> dict[str, Any]:
        return self.api.get_posts()

    def get_post_comments(self, post_id: str) -> dict[str, Any]:
        return self.api.get_comments(post_id)

    def delete_post(self, post_id: str) -> dict[str, Any]:
        return self.api.delete_post(post_id)

    def delete_comment(self, comment_id: str) -> dict[str, Any]:
        return self.api.delete_comment(comment_id)

    def hide_comment(self, comment_id: str) -> dict[str, Any]:
        return self.api.hide_comment(comment_id)

    def unhide_comment(self, comment_id: str) -> dict[str, Any]:
        return self.api.unhide_comment(comment_id)

    def delete_comment_from_post(self, post_id: str, comment_id: str) -> dict[str, Any]:
        return self.api.delete_comment(comment_id)

    def filter_negative_comments(self, comments: dict[str, Any]) -> list[dict[str, Any]]:
        keywords = ["bad", "terrible", "awful", "hate", "dislike", "problem", "issue"]
        return [c for c in comments.get("data", []) if any(k in c.get("message", "").lower() for k in keywords)]

    def get_number_of_comments(self, post_id: str) -> int:
        return len(self.api.get_comments(post_id).get("data", []))

    def get_number_of_likes(self, post_id: str) -> int:
        return self.api._request("GET", post_id, {"fields": "likes.summary(true)"}).get("likes", {}).get("summary", {}).get("total_count", 0)

    def get_post_insights(self, post_id: str) -> dict[str, Any]:
        # Graph API rejects the ENTIRE multi-metric request if even one metric
        # in the comma-joined list is invalid, so this list is a verified
        # allowlist, not a wishlist. post_impressions* (removed in v25+) and
        # post_engaged_users (retired permanently by Meta 2024-09-16, no
        # replacement) were both breaking this call — do not add either back.
        # Use get_post_impressions_paid/_organic for the ads/organic split
        # via the is_from_ads breakdown, and get_post_engaged_users for an
        # estimated engaged-users figure.
        metrics = [
            "post_media_view", "post_total_media_view_unique", "post_clicks",
            "post_reactions_by_type_total",
        ]
        return self.api.get_bulk_insights(post_id, metrics)

    def get_post_impressions(self, post_id: str) -> dict[str, Any]:
        """Total content views. Replaces post_impressions, removed in Graph API v25+."""
        return self.api.get_insights(post_id, "post_media_view")

    def get_post_impressions_unique(self, post_id: str) -> dict[str, Any]:
        """Unique content viewers. Replaces post_impressions_unique, removed in Graph API v25+."""
        return self.api.get_insights(post_id, "post_total_media_view_unique")

    def get_post_impressions_paid(self, post_id: str) -> dict[str, Any]:
        """Views attributed to ads, via post_media_view's is_from_ads
        breakdown. Replaces post_impressions_paid, removed in Graph API v25+.
        Falls back to the raw breakdown response if Meta's response shape
        doesn't match what extract_breakdown_value parses for."""
        raw = self.api.get_insights(post_id, "post_media_view", breakdown="is_from_ads")
        value = self.api.extract_breakdown_value(raw, "true")
        return raw if value is None else {"post_id": post_id, "metric": "post_media_view", "is_from_ads": True, "value": value}

    def get_post_impressions_organic(self, post_id: str) -> dict[str, Any]:
        """Views not attributed to ads, via post_media_view's is_from_ads
        breakdown. Replaces post_impressions_organic, removed in Graph API v25+."""
        raw = self.api.get_insights(post_id, "post_media_view", breakdown="is_from_ads")
        value = self.api.extract_breakdown_value(raw, "false")
        return raw if value is None else {"post_id": post_id, "metric": "post_media_view", "is_from_ads": False, "value": value}

    def get_post_engaged_users(self, post_id: str) -> dict[str, Any]:
        """Meta permanently retired post_engaged_users on 2024-09-16 with no
        replacement metric — it is gone, not renamed. Returns a computed
        ESTIMATE (comments + shares + total reactions) instead, clearly
        labeled as such; this is not an official Meta engaged-users count and
        may undercount versus Meta's original metric (no click dedup)."""
        num_comments = self.get_number_of_comments(post_id)
        num_shares = self.api.get_post_share_count(post_id)
        reactions = self.get_post_reactions_breakdown(post_id)
        num_reactions = sum(v for v in reactions.values() if isinstance(v, (int, float)))
        return {
            "post_id": post_id,
            "is_estimate": True,
            "estimated_engaged_users": num_comments + num_shares + num_reactions,
            "note": "Meta retired post_engaged_users on 2024-09-16 with no replacement metric. "
                    "This is a computed approximation (comments + shares + reactions), not an official Meta metric.",
            "components": {"comments": num_comments, "shares": num_shares, "reactions": num_reactions},
        }

    def get_post_clicks(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_clicks")

    def get_post_reactions_like_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_like_total")

    def get_post_reactions_love_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_love_total")

    def get_post_reactions_wow_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_wow_total")

    def get_post_reactions_haha_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_haha_total")

    def get_post_reactions_sorry_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_sorry_total")

    def get_post_reactions_anger_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_anger_total")

    def get_post_top_commenters(self, post_id: str) -> list[dict[str, Any]]:
        comments = self.get_post_comments(post_id).get("data", [])
        counter = {}
        for comment in comments:
            user_id = comment.get("from", {}).get("id")
            if user_id:
                counter[user_id] = counter.get(user_id, 0) + 1
        return sorted([{"user_id": k, "count": v} for k, v in counter.items()], key=lambda x: x["count"], reverse=True)

    def post_image_to_facebook(self, image_url: str, caption: str) -> dict[str, Any]:
        return self.api.post_image_to_facebook(image_url, caption)

    def send_dm_to_user(self, user_id: str, message: str) -> dict[str, Any]:
        return self.api.send_dm_to_user(user_id, message)
    
    def update_post(self, post_id: str, new_message: str) -> dict[str, Any]:
        return self.api.update_post(post_id, new_message)

    def schedule_post(self, message: str, publish_time: int) -> dict[str, Any]:
        return self.api.schedule_post(message, publish_time)

    def get_page_fan_count(self) -> int:
        return self.api.get_page_fan_count()

    def get_post_share_count(self, post_id: str) -> int:
        return self.api.get_post_share_count(post_id)

    def get_post_reactions_breakdown(self, post_id: str) -> dict[str, Any]:
        """Return counts for all reaction types on a post."""
        metrics = [
            "post_reactions_like_total",
            "post_reactions_love_total",
            "post_reactions_wow_total",
            "post_reactions_haha_total",
            "post_reactions_sorry_total",
            "post_reactions_anger_total",
        ]
        raw = self.api.get_bulk_insights(post_id, metrics)
        results: dict[str, Any] = {}
        for item in raw.get("data", []):
            name = item.get("name")
            value = item.get("values", [{}])[0].get("value")
            results[name] = value
        return results

    def bulk_delete_comments(self, comment_ids: list[str]) -> list[dict[str, Any]]:
        """Delete multiple comments and return their results."""
        results = []
        for cid in comment_ids:
            res = self.api.delete_comment(cid)
            results.append({"comment_id": cid, "result": res})
        return results

    def bulk_hide_comments(self, comment_ids: list[str]) -> list[dict[str, Any]]:
        """Hide multiple comments and return their results."""
        results = []
        for cid in comment_ids:
            res = self.api.hide_comment(cid)
            results.append({"comment_id": cid, "result": res})
        return results

    def bulk_unhide_comments(self, comment_ids: list[str]) -> list[dict[str, Any]]:
        """Unhide multiple comments and return their results."""
        results = []
        for cid in comment_ids:
            res = self.api.unhide_comment(cid)
            results.append({"comment_id": cid, "result": res})
        return results

    def get_comment_replies(self, comment_id: str) -> dict[str, Any]:
        return self.api.get_comment_replies(comment_id)

    def get_post_permalink(self, post_id: str) -> dict[str, Any]:
        return self.api.get_post_permalink(post_id)

    def get_scheduled_posts(self) -> dict[str, Any]:
        return self.api.get_scheduled_posts()

    def get_page_info(self) -> dict[str, Any]:
        return self.api.get_page_info()
