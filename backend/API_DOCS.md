# FloodVision AI – Backend API Documentation

This document provides the integration specifications for connecting the Flutter application to the FastAPI backend infrastructure.

---

## 🔐 Authentication & Security Requirements

All protected endpoints require a verified Firebase ID token to be sent in the HTTP request headers. If the token is missing or invalid, the backend will return a `401 Unauthorized` response.

### How to send the Firebase token in Flutter
Before invoking any protected endpoint, retrieve the current user's ID token and append it to the request headers:

```dart
// Flutter Implementation Snippet
final token = await FirebaseAuth.instance.currentUser?.getIdToken();

final response = await http.post(
  Uri.parse('[https://your-backend-url.com/api/reports/submit](https://your-backend-url.com/api/reports/submit)'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({ ... }),
);