diff --git app/uploaders/unprocessed_image.rb app/uploaders/unprocessed_image.rb
index b662f3b..1f11b50 100644
--- app/uploaders/unprocessed_image.rb
+++ app/uploaders/unprocessed_image.rb
@@ -7,16 +7,20 @@
 class UnprocessedImage < CarrierWave::Uploader::Base
   include CarrierWave::MiniMagick
 
+  def store_dir
+    '/data/diaspora/uploads'
+  end
+
+  def cache_dir
+    '/data/diaspora/cache'
+  end
+
   attr_accessor :strip_exif
 
   def strip_exif
     @strip_exif || false
   end
 
-  def store_dir
-    "uploads/images"
-  end
-
   def extension_whitelist
     %w[jpg jpeg png gif]
   end
