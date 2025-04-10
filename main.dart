import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(FingerprintApp());
}

class FingerprintApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: FingerprintScreen(),
    );
  }
}

class FingerprintScreen extends StatefulWidget {
  @override
  _FingerprintScreenState createState() => _FingerprintScreenState();
}

class _FingerprintScreenState extends State<FingerprintScreen> {
  File? _image;
  final picker = ImagePicker();

  Future pickImage() async {
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      setState(() {
        _image = File(pickedFile.path);
      });
    }
  }

  Future registerFingerprint() async {
    if (_image == null) return;
    var request = http.MultipartRequest('POST', Uri.parse('http://10.0.2.2:5000/register'));
    request.files.add(await http.MultipartFile.fromPath('file', _image!.path));
    var response = await request.send();
    var responseData = await response.stream.bytesToString();
    var result = jsonDecode(responseData);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'])));
  }

  Future verifyFingerprint() async {
    if (_image == null) return;
    var request = http.MultipartRequest('POST', Uri.parse('http://10.0.2.2:5000/verify'));
    request.files.add(await http.MultipartFile.fromPath('file', _image!.path));
    var response = await request.send();
    var responseData = await response.stream.bytesToString();
    var result = jsonDecode(responseData);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'])));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Fingerprint System')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _image == null ? Text('No image selected') : Image.file(_image!),
            SizedBox(height: 20),
            ElevatedButton(onPressed: pickImage, child: Text('Pick Image')),
            ElevatedButton(onPressed: registerFingerprint, child: Text('Register')),
            ElevatedButton(onPressed: verifyFingerprint, child: Text('Verify')),
          ],
        ),
      ),
    );
  }
}
