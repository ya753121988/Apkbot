import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
void main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('FlixBoxs')),body:WebViewWidget(controller:WebViewController()..loadRequest(Uri.parse('https://flixboxsmovies.blogspot.com/'))))));