import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Fingerprint Recognition',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
        scaffoldBackgroundColor: Colors.grey[100],
        textTheme: const TextTheme(
          bodyMedium: TextStyle(fontSize: 16),
        ),
      ),
      home: const FingerprintScreen(),
    );
  }
}

class FingerprintScreen extends StatefulWidget {
  const FingerprintScreen({super.key});

  @override
  State<FingerprintScreen> createState() => _FingerprintScreenState();
}

class _FingerprintScreenState extends State<FingerprintScreen> {
  File? _capturedImage;
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _usernameController = TextEditingController();
  final http.Client _httpClient = http.Client();

  Future<void> _captureImage() async {
    final pickedFile = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 80,
      preferredCameraDevice: CameraDevice.rear,
    );

    if (pickedFile != null) {
      setState(() {
        _capturedImage = File(pickedFile.path);
      });
    }
  }

  Future<void> _registerFingerprint() async {
    String username = _usernameController.text.trim();
    if (username.isEmpty || _capturedImage == null) {
      _showPopup("Error", "Please enter a username and capture an image.");
      return;
    }

    try {
      var request = http.MultipartRequest(
          'POST', Uri.parse("http://172.20.10.2:5000/register"));
      request.fields['username'] = username;
      request.files.add(await http.MultipartFile.fromPath('file', _capturedImage!.path));

      var response = await _httpClient.send(request);
      var responseBody = await response.stream.bytesToString();
      var jsonResponse = await compute(jsonDecode, responseBody);

      _showPopup("Success", jsonResponse["message"]);
    } catch (e) {
      _showPopup("Error", "Unable to register fingerprint.");
    }
  }

  Future<void> _verifyFingerprint() async {
    if (_capturedImage == null) {
      _showPopup("Error", "Please capture an image first.");
      return;
    }

    try {
      var request = http.MultipartRequest(
          'POST', Uri.parse("http://172.20.10.2:5000/verify"));
      request.files.add(await http.MultipartFile.fromPath('file', _capturedImage!.path));

      var response = await _httpClient.send(request);
      var responseBody = await response.stream.bytesToString();
      var jsonResponse = await compute(jsonDecode, responseBody);

      if (jsonResponse.containsKey("user")) {
        _showPopup("Verified", "Match found! Verified user: ${jsonResponse["user"]}\nAccuracy: ${jsonResponse["accuracy"]}%");
      } else {
        _showPopup("Not Found", jsonResponse["message"]);
      }
    } catch (e) {
      _showPopup("Error", "Unable to verify fingerprint.");
    }
  }

  Future<void> _showCurrentUsers() async {
    try {
      final response = await _httpClient.get(Uri.parse("http://172.20.10.2:5000/users"));
      if (response.statusCode == 200) {
        var jsonResponse = await compute(jsonDecode, response.body);
        List users = jsonResponse["users"];

        String userList = users.isEmpty
            ? "No users registered yet!"
            : users.map((user) => "${user['id']}: ${user['username']}").join("\n");

        _showPopup("Current Users", userList);
      } else {
        _showPopup("Error", "Failed to fetch users.");
      }
    } catch (e) {
      _showPopup("Error", "Error fetching users.");
    }
  }

  void _showPopup(String title, String content) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        content: Text(content, style: const TextStyle(fontSize: 16)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Close", style: TextStyle(color: Colors.deepPurple)),
          ),
        ],
      ),
    );
  }

  Widget _buildButton(IconData icon, String label, VoidCallback onPressed, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          icon: Icon(icon, color: Colors.white),
          label: Text(label, style: const TextStyle(color: Colors.white)),
          onPressed: onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: color,
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Fingerprint Recognition"),
        centerTitle: true,
        backgroundColor: Colors.deepPurple,
        elevation: 5,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: _usernameController,
                  decoration: InputDecoration(
                    labelText: "Enter Username",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 20),
                if (_capturedImage != null)
                  Image.file(_capturedImage!, width: 220, height: 220, fit: BoxFit.cover)
                else
                  const Icon(Icons.camera_alt, size: 100, color: Colors.deepPurple),
                const SizedBox(height: 20),
                _buildButton(Icons.camera, "Capture Fingerprint", _captureImage, Colors.purpleAccent),
                _buildButton(Icons.fingerprint, "Register", _registerFingerprint, Colors.green),
                _buildButton(Icons.verified, "Verify", _verifyFingerprint, Colors.blue),
                _buildButton(Icons.list, "Current Users", _showCurrentUsers, Colors.orange),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
