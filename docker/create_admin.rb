# Criar conta e usuário admin para TikTrend Finder
account = Account.find_or_create_by!(name: 'TikTrend Finder') do |a|
  a.locale = 'pt_BR'
end

user = User.find_or_create_by!(email: 'admin@tiktrendfinder.local') do |u|
  u.password = 'Admin@Didin#2024!'
  u.password_confirmation = 'Admin@Didin#2024!'
  u.name = 'Admin Didin'
  u.confirmed_at = Time.now
end

AccountUser.find_or_create_by!(account: account, user: user) do |au|
  au.role = :administrator
end

# Gerar API Access Token para integração
access_token = user.access_token&.token || user.create_access_token!.token

puts '=' * 60
puts 'CHATWOOT ADMIN CRIADO COM SUCESSO!'
puts '=' * 60
puts "Email: admin@tiktrendfinder.local"
puts "Senha: Admin@Didin#2024!"
puts "Account ID: #{account.id}"
puts "API Access Token: #{access_token}"
puts '=' * 60
