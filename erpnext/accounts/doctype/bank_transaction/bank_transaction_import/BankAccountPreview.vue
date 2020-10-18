<template>
    <div class="account-preview">
        <div class="text-center border rounded" :class="selectedAccount == account.name ? 'active' : ''" @click="selectAccount(account.name)">
			<img
				v-if="account.logo"
				:src="account.logo"
				:alt="account.name"
				style="object-fit: cover; height: 100%; max-height: 100px;"
			>
			<div class="flex align-center justify-center" style="height: 100%;" v-else>
				<i class="uil uil-university text-extra-muted" style="font-size: 4rem;"></i>
			</div>

            <div class="account-info">
                <p class="strong">{{ account.account_name }}</p>
                <p>{{ account.bank }}</p>
                <p class="text-muted">{{ account.company }}</p>
            </div>
		</div>
    </div>
</template>

<script>
export default {
    name: 'BankAccountPreview',
    props: {
        account: {
            type: Object,
            default: {}
        },
        selectedAccount: {
            type: String,
            default: null
        }
    },
    methods: {
        selectAccount: function(account) {
            this.$emit('accountSelected', account)
        }
    }
    
}
</script>

<style lang='scss' scoped>

.account-preview {
    width: 25%;
	padding-right: 15px;
	padding-bottom: 15px;
	position: relative;
    cursor: pointer;

    .active {
        border-color: #6195FF;
	    box-shadow: 0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -2px rgba(0,0,0,.05);
    }

    .account-info {
        p {
            margin: 5px 0px;
        }
    }
}

</style>