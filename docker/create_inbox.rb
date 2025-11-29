# Criar inbox API para integração com Evolution API
account = Account.find(1)

# Criar inbox do tipo API
inbox = Inbox.find_or_create_by!(
  account: account,
  name: 'WhatsApp Didin'
) do |i|
  i.channel = Channel::Api.create!(account: account)
end

# Gerar webhook URL para Evolution API enviar mensagens
api_inbox = inbox.channel

puts '=' * 60
puts 'CHATWOOT INBOX CRIADO PARA WHATSAPP'
puts '=' * 60
puts "Inbox ID: #{inbox.id}"
puts "Inbox Name: #{inbox.name}"
puts "Channel Type: #{inbox.channel_type}"
puts "Channel ID: #{api_inbox.id}"
puts "Webhook Token: #{api_inbox.identifier}"
puts ""
puts "Webhook URL para Evolution API:"
puts "POST http://chatwoot:3000/webhooks/api/#{api_inbox.identifier}"
puts '=' * 60
