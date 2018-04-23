# frozen_string_literal: true

module Api
  module OpenidConnect
    class IdTokenConfig
      config_dir = ENV["DIASPORA_CONFIG_DIR"] || File.join(Rails.root, "config")
      key_file_path = File.join(config_dir, "oidc_key.pem")
      if File.exist?(key_file_path)
        private_key = OpenSSL::PKey::RSA.new(File.read(key_file_path))
      else
        private_key = OpenSSL::PKey::RSA.new(4096)
        File.write key_file_path, private_key.to_pem
        File.chmod(0600, key_file_path)
      end
      PRIVATE_KEY = private_key
      PUBLIC_KEY = private_key.public_key
    end
  end
end
