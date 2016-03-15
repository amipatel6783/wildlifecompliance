from django.test import TestCase
from mixer.backend.django import mixer
from customers.models import Customer, Address


class CustomerTest(TestCase):

    def setUp(self):
        super(CustomerTest, self).setUp()
        self.user = mixer.blend(Customer)

    def test_str(self):
        """Test the Customer __str__ method returns email
        """
        self.assertEqual(self.user.email, str(self.user))

    def test_create_user_no_email(self):
        """
        """
        self.assertRaises(ValueError, Customer.objects.create_user)

    def test_create_user(self):
        """Test the Customer create_user method
        """
        u = Customer.objects.create_user('test@email.com')
        self.assertTrue(isinstance(u, Customer))

    def test_create_superuser(self):
        """Test the Customer create_superuser method
        """
        u = Customer.objects.create_superuser('superuser@email.com', '')
        self.assertTrue(isinstance(u, Customer))

    def test_get_full_name(self):
        """Test the Customer get_full_name method
        """
        n = self.user.get_full_name()
        self.assertEqual(n, '{} {}'.format(self.user.first_name, self.user.last_name))

    def test_short_name(self):
        """Test short_name returns email or first_name
        """
        self.assertEqual(self.user.get_short_name(), self.user.first_name)
        self.user.first_name = ''
        self.user.save()
        self.assertEqual(self.user.get_short_name(), self.user.email)


class AddressTest(TestCase):

    def setUp(self):
        super(AddressTest, self).setUp()
        self.address1 = mixer.blend(Address)

    def test_prop_name(self):
        """Test the Address name property
        """
        a = self.address1
        name = '{} {}'.format(a.first_name, a.last_name)
        self.assertEqual(name, a.name)

    def test_prop_join_fields(self):
        """Test the Address join_fields property
        """
        a = self.address1
        joined = '{}:{}'.format(a.first_name, a.last_name)
        self.assertEqual(
            joined, a.join_fields(['first_name', 'last_name'], ':'))

    def test_clean(self):
        """Test the Address clean method
        """
        a = self.address1
        a.first_name = a.first_name + ' '
        a.save()
        self.assertTrue(a.first_name.endswith(' '))
        a.clean()
        self.assertFalse(a.first_name.endswith(' '))

    def test_str(self):
        """Test the Address __str__ method returns summary property
        """
        a = self.address1
        self.assertEqual(a.summary, str(a))

