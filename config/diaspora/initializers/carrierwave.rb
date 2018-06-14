CarrierWave.configure do |config|
    config.root = '/data/diaspora'
    config.store_dir = '/data/diaspora/uploads'
    config.cache_dir = '/data/diaspora/cache'
    config.storage = :file
end